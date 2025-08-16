
import {
    fetchUtils,
    DataProvider,
    GetListResult,
    GetListParams,
    RaRecord,
    GetManyParams,
    GetManyResult, GetOneParams, GetOneResult, UpdateResult, UpdateParams,
    HttpError, CreateResult, CreateParams,
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

    return fetchUtils.fetchJson(url, optionsWithToken).catch((error: HttpError) => {
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

    constructor(runtimeProps: RuntimeProps) {
        this.runtimeProps = runtimeProps;
        this.dataProvider = jsonServerProvider(runtimeProps.ADMIN_API_BACKEND_URL + "/v1", retryHttpClient);
    }

    async getList<T extends RaRecord>(resource: string, params: GetListParams): Promise<GetListResult<T>> {

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

        return this.dataProvider.getList<T>(addTrailingSlash(resource), params);
    }

    async getOne<T extends RaRecord>(resource: string, params: GetOneParams): Promise<GetOneResult<T>>
    {
        if (resource === 'document-metadata') {
            const docId = params.id;
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/metadata/document/${docId}`;
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T,
                };
            }
            catch (error) {
                handleHttpError(error, 'Failed to load document metadata');
            }
        }

        return this.dataProvider.getOne(resource, params);
    }

    async getMany<T extends RaRecord>(resource: string, params: GetManyParams): Promise<GetManyResult<T>> {
        if (resource === 'endorsees') {
            console.log("endorsees -> users");
            return this.dataProvider.getMany<T>("users/", params);
        }
        else if (resource === 'document-metadata') {
            const id = params.ids[0];
            const url = `${this.runtimeProps.ADMIN_API_BACKEND_URL}/v1/metadata/document/${id}`;
            try {
                const response = await retryHttpClient(url);
                return {
                    data: [await response.json] as T[],
                };
            }
            catch (error) {
                console.log("document-metadata: " + JSON.stringify(error));
                handleHttpError(error, 'Failed to load document metadata');
            }
            finally {
                console.log("document-metadata: done");
            }
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
        return this.dataProvider.create(resource, params);
    }

    delete: typeof this.dataProvider.delete = (resource, params) => this.dataProvider.delete(resource, params);
    deleteMany: typeof this.dataProvider.deleteMany = (resource, params) => this.dataProvider.deleteMany(resource, params);
}

export default adminApiDataProvider;
