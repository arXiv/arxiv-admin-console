
import {
    fetchUtils,
    DataProvider,
    GetListResult,
    GetListParams,
    RaRecord,
    GetManyParams,
    GetManyResult, GetOneParams, GetOneResult, UpdateResult, UpdateParams,
    HttpError, CreateResult, CreateParams, DeleteResult, DeleteParams, DeleteManyResult, DeleteManyParams,
} from 'react-admin';
import jsonServerProvider from 'ra-data-json-server';
import {paths as aaaApi} from "./types/aaa-api";
import {RuntimeProps} from "./RuntimeContext";

type EmailChangeRequestBodyT = aaaApi['/account/{user_id}/email']['put']['requestBody']['content']['application/json'];
type UserAuthzT = aaaApi['/account/{user_id}/authorization']['put']['requestBody']['content']['application/json'];

const addTrailingSlash = (url: string) => {
    return url.endsWith('/') ? url : `${url}/`;
};

const handleHttpError = (error: any, defaultMessage: string = 'An error occurred') => {
    if (error && typeof error === 'object') {
        // Check if it has a status property (like HttpError)
        if ('status' in error && error.status) {
            throw error;
        }

        // Create a new HttpError with type-safe property access
        const errorObj = error as Record<string, any>;
        const errorMessage =
            'message' in errorObj && typeof errorObj.message === 'string'
                ? errorObj.message
                : defaultMessage;

        throw new HttpError(
            errorMessage,
            'status' in errorObj && typeof errorObj.status === 'number' ? errorObj.status : 500,
            'body' in errorObj ? errorObj.body : {}
        );
    }

    // If error is not an object or doesn't have expected properties
    throw new HttpError(
        defaultMessage,
        500,
        {}
    );
};


let retryCount = 0;

// interface HttpError extends Error {
//     status: number;
//     body?: any;
// }

const retryHttpClient = (url: string, options: fetchUtils.Options = {}) => {
    const access_token = localStorage.getItem('access_token');
    const token_type = localStorage.getItem('token_type') || "Bearer";

    const optionsWithToken = {
        ...options,
        user: access_token
            ? { authenticated: true, token: token_type + " " + access_token }
            : options.user, // Keep original user if no token
    };

    return fetchUtils.fetchJson(url, optionsWithToken)
        .then(response => {
            // Handle 204 No Content responses by providing expected structure
            if (response.status === 204) {
                console.log('🔄 Handling 204 No Content response for:', url);
                // For DELETE operations, provide an appropriate response structure
                if (options.method === 'DELETE') {
                    return {
                        ...response,
                        json: [], // Empty array for deleteMany operations
                        status: 200, // Convert to 200 so ra-data-json-server doesn't complain
                    };
                }
            }
            return response;
        })
        .catch((error: HttpError) => {
            if (error.status === 500 && retryCount < 3) {
                retryCount += 1;
                // Optionally retry the request or handle it gracefully
                return fetchUtils.fetchJson(url, optionsWithToken);
            } else {
                retryCount = 0;
                throw error;
            }
        });
};

class adminApiDataProvider implements DataProvider {
    private dataProvider: DataProvider;
    private runtimeProps: RuntimeProps;
    private bulkDeletedIds: Set<string> = new Set(); // Track bulk deleted IDs

    constructor(runtimeProps: RuntimeProps) {
        this.runtimeProps = runtimeProps;
        this.dataProvider = jsonServerProvider(runtimeProps.ADMIN_API_BACKEND_URL + "/v1", retryHttpClient);
    }

    async getList<T extends RaRecord>(resource: string, params: GetListParams): Promise<GetListResult<T>> {
        console.log(`getList ${resource}:`, params);

        if (resource === 'subject_class' && params.filter.archive) {
            const { archive } = params.filter;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/categories/${archive}/subject-class/`;
            console.log("subject_class API " +  url);
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T[],
                    total: response.json.length,
                };
            }
            catch (error) {
                handleHttpError(error, 'Failed to load subject classes');
            }
        }
        else if (resource === 'endorsees') {
            console.log("endorsees -> users");
            return this.dataProvider.getList<T>("users", params);
        }
        else if (resource === 'paper_owners_user_doc') {
            const { user_id } = params.filter;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/paper_owners/user/${user_id}`;
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T[],
                    total: response.json.length,
                };
            }
            catch (error) {
                handleHttpError(error, 'Failed to load paper owners');
            }
        }
        else if (resource === 'can_submit_to') {
            const { user_id } = params.filter;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/users/${user_id}/can-submit-to`;
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T[],
                    total: response.json.length,
                };
            }
            catch (error) {
                handleHttpError(error, 'Failed to load submission permissions');
            }
        }
        else if (resource === 'can_endorse_for') {
            const { user_id } = params.filter;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/users/${user_id}/can-endorse-for`;
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T[],
                    total: response.json.length,
                };
            }
            catch (error) {
                handleHttpError(error, 'Failed to load endorsement permissions');
            }
        }
        else if (resource === 'user_email_history') {
            const { user_id } = params.filter;
            const baseUrl = `${this.runtimeProps.AAA_URL}/account/${user_id}/email/history`;

            const searchParams = new URLSearchParams();

            if (params.pagination) {
                const { page, perPage } = params.pagination;
                // Calculate _start and _end for server-side pagination
                const start = (page - 1) * perPage;
                const end = page * perPage;
                searchParams.append('_start', start.toString());
                searchParams.append('_end', end.toString());
            }

            // Handle sorting if provided
            if (params.sort) {
                const { field, order } = params.sort;
                searchParams.append('_sort', field);
                searchParams.append('_order', order.toLowerCase());
            }

            // Construct the final URL
            const url = searchParams.toString()
                ? `${baseUrl}?${searchParams.toString()}`
                : baseUrl;

            try {
                const response = await retryHttpClient(url);
                const totalCount = response.headers.get('X-Total-Count')
                    ? parseInt(response.headers.get('X-Total-Count') || '0', 10)
                    : response.json.length;

                return {
                    data: response.json as T[],
                    total: totalCount,
                };
            }
            catch (error) {
                handleHttpError(error, 'Failed to load email history');
            }
        }
        else if (resource === 'document-metadata-latest') {
            return this.dataProvider.getList<T>("documents/metadata/latest", params);
        }
        return this.dataProvider.getList<T>(addTrailingSlash(resource), params);
    }

    async getOne<T extends RaRecord>(resource: string, params: GetOneParams): Promise<GetOneResult<T>>
    {
        // console.log(`getOne ${resource}:`, params);
        if (resource === 'document-metadata-latest') {
            const { id, ...restParams } = params;
            return this.dataProvider.getOne<T>(`documents/${id}/metadata/latest`, {...restParams, id: ""});
        }

        return this.dataProvider.getOne(resource, params);
    }

    async getMany<T extends RaRecord>(resource: string, params: GetManyParams): Promise<GetManyResult<T>> {
        console.log(`getMany ${resource}:`, params);

        if (resource === 'endorsees') {
            console.log("endorsees -> users");
            return this.dataProvider.getMany<T>("users/", params);
        }
        else if (resource === 'document-metadata-latest') {
            return this.dataProvider.getMany<T>("documents/metadata/latest", params);
        }

        return this.dataProvider.getMany<T>(addTrailingSlash(resource), params);
    }

    async update<T extends RaRecord>(resource: string, params: UpdateParams):  Promise<UpdateResult<T>>
    {
        if (resource === 'aaa_user_email') {
            console.log("Update user email via AAA API");
            const user_id = params.id;

            const body : EmailChangeRequestBodyT = {
                email: params.data.email,
                new_email: params.data.new_email,
            };

            try {
                const putEmailChange = this.runtimeProps.aaaFetcher.path('/account/{user_id}/email').method('put').create();
                const response = await putEmailChange({
                    user_id: user_id as string,
                    ...body
                });

                return {data: response.data as unknown as T};
            }
            catch (error) {
                handleHttpError(error, 'Failed to update email');
            }
        }
        else if (resource === 'aaa_user_name') {
            console.log("Update user name via AAA API");
            const user_id = params.id;

            const body  = {
                first_name: params.data.first_name,
                last_name: params.data.last_name,
                suffix_name: params.data.suffix_name,
                username: params.data.username,
                comment: params.data.comment,
            };

            try {
                const putUserNameChange = this.runtimeProps.aaaFetcher.path('/account/{user_id}/name').method('put').create();
                const response = await putUserNameChange({
                    user_id: user_id as string,
                    ...body
                });

                return {data: response.data as unknown as T};
            }
            catch (error) {
                handleHttpError(error, 'Failed to update user name');
            }
        }
        else if (resource === 'user-authorization') {
            console.log("Update user authorization via AAA API");
            const user_id = params.id;

            const body : UserAuthzT = {
                [params.data.authorizationName]: params.data.authorizationValue,
                comment: params.data.comment,
            };

            try {
                const putUserAuthorization = this.runtimeProps.aaaFetcher.path('/account/{user_id}/authorization').method('put').create();
                const response = await putUserAuthorization({
                    user_id: user_id as string,
                    ...body
                });

                return {data: response.data as unknown as T};
            }
            catch (error) {
                handleHttpError(error, 'Failed to update authorization');
            }

        }

        return this.dataProvider.update(resource, params);
    }

    getManyReference: typeof this.dataProvider.getManyReference = (resource, params) => this.dataProvider.getManyReference(resource, params);
    updateMany: typeof this.dataProvider.updateMany= (resource, params) => this.dataProvider.updateMany(resource, params);

    async create<T extends RaRecord>(resource: string, params: CreateParams):  Promise<CreateResult<T>> {
        if (resource === "user-comment") {
            const {data, meta} = params;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/users/${meta.userId}/comment`;

            try {
                const response = await retryHttpClient(url, {
                    method: 'POST',
                    body: JSON.stringify(data),
                });

                return {data: response.json as T};
            }
            catch (error) {
                handleHttpError(error, 'Failed to create user comment');
            }

        }
        return this.dataProvider.create(addTrailingSlash(resource), params);
    }

    async delete<T extends RaRecord>(resource: string, params: DeleteParams): Promise<DeleteResult<T>> {
        console.log(`🗑️ DELETE ${resource}:`, params);
        const result = await this.dataProvider.delete(resource, params);
        console.log(`✅ DELETE ${resource} succeeded:`, result);
        return result;
    }

    async deleteMany<T extends RaRecord>(resource: string, params: DeleteManyParams): Promise<DeleteManyResult<T>> {
        console.log(`🗑️ DELETE_MANY ${resource}:`, params);
        
        // Handle email_patterns with purpose-based path
        if (resource === 'email_patterns' && params.meta?.purpose) {
            const { purpose } = params.meta;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/email_patterns/${purpose}`;
            
            try {
                const response = await retryHttpClient(url, {
                    method: 'DELETE',
                    body: JSON.stringify({ ids: params.ids }),
                });
                
                // Track bulk deleted IDs to prevent individual delete calls
                params.ids.forEach(id => {
                    this.bulkDeletedIds.add(`${resource}:${id}`);
                });
                
                console.log(`✅ DELETE_MANY ${resource} with purpose ${purpose} succeeded`);
            } catch (error) {
                console.error(`❌ DELETE_MANY ${resource} with purpose ${purpose} failed:`, error);
                handleHttpError(error, `Failed to delete ${resource} with purpose ${purpose}`);
            }
            return { data: params.ids as T["id"][] };
        }
        
        const result = await this.dataProvider.deleteMany(resource, params);
        console.log(`✅ DELETE_MANY ${resource} succeeded:`, result);
        return result;
    }
}

export default adminApiDataProvider;
