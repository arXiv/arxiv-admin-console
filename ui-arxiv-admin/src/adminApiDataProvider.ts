
import {
    fetchUtils,
    DataProvider,
    GetListResult,
    GetListParams,
    RaRecord,
    GetManyParams,
    GetManyResult, GetOneParams, GetOneResult
} from 'react-admin';
import jsonServerProvider from 'ra-data-json-server';

const addTrailingSlash = (url: string) => {
    return url.endsWith('/') ? url : `${url}/`;
};

let retryCount = 0;

interface HttpError extends Error {
    status: number;
    body?: any;
}

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
    private api: string;
    constructor(api: string) {
        this.api = api;
        this.dataProvider = jsonServerProvider(api, retryHttpClient);
    }
    async getList<T extends RaRecord>(resource: string, params: GetListParams): Promise<GetListResult<T>> {

        if (resource === 'subject_class' && params.filter.archive) {
            const { archive } = params.filter;
            const url = `${this.api}/categories/${archive}/subject-class/`;
            console.log("subject_class API " +  url);
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T[],
                    total: response.json.length,
                };
            }
            catch (error) {
                return {
                    data: [] as T[],
                    total: 0,
                };
            }
        }
        else if (resource === 'endorsees') {
            console.log("endorsees -> users");
            return this.dataProvider.getList<T>("users", params);
        }
        else if (resource === 'paper_owners_user_doc') {
            const { user_id } = params.filter;
            const url = `${this.api}/paper_owners/user/${user_id}`;
            try {
                const response = await retryHttpClient(url);
                return {
                    data: response.json as T[],
                    total: response.json.length,
                };
            }
            catch (error) {
                return {
                    data: [] as T[],
                    total: 0,
                };
            }
        }

        return this.dataProvider.getList<T>(addTrailingSlash(resource), params);
    }

    async getOne<T extends RaRecord>(resource: string, params: GetOneParams): Promise<GetOneResult<T>>
    {
        return this.dataProvider.getOne(resource, params);
    }

    async getMany<T extends RaRecord>(resource: string, params: GetManyParams): Promise<GetManyResult<T>> {
        if (resource === 'endorsees') {
            console.log("endorsees -> users");
            return this.dataProvider.getMany<T>("users/", params);
        }
        return this.dataProvider.getMany<T>(addTrailingSlash(resource), params);
    }

    getManyReference: typeof this.dataProvider.getManyReference = (resource, params) => this.dataProvider.getManyReference(resource, params);
    create: typeof this.dataProvider.create = (resource, params) => this.dataProvider.create(resource, params);
    update: typeof this.dataProvider.update = (resource, params) => this.dataProvider.update(resource, params);
    updateMany: typeof this.dataProvider.updateMany= (resource, params) => this.dataProvider.updateMany(resource, params);
    delete: typeof this.dataProvider.delete = (resource, params) => this.dataProvider.delete(resource, params);
    deleteMany: typeof this.dataProvider.deleteMany = (resource, params) => this.dataProvider.deleteMany(resource, params);
}

export default adminApiDataProvider;
