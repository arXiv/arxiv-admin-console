import React, { createContext, useState, useEffect } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import {Box} from '@mui/material';
import {paths} from "./types/aaa-api";
import {paths as adminPaths} from "./types/admin-api";
import { Fetcher } from 'openapi-typescript-fetch';


export interface ArxiURLs
{
    CheckSubmissionLink: string;
    JiraLink: string;
}

/*
https://www.npmjs.com/package/uri-templates
 */
const arXivURLs: ArxiURLs = {
    CheckSubmissionLink: '{+arxivCheck}/submit/{submissionId}',
    JiraLink: '{+jira}/browse/{issueKey}',
}


export interface RuntimeProps
{
    AAA_URL: string;
    ADMIN_API_BACKEND_URL: string;
    ADMIN_APP_ROOT: string;
    ARXIV_COOKIE_NAME: string;
    TAPIR_COOKIE_NAME: string;
    ARXIV_KEYCLOAK_COOKIE_NAME: string;
    ARXIV_CHECK: string;
    URLS: ArxiURLs;
    updateEnv: (key: string, value: string) => void;
    aaaFetcher: ReturnType<typeof Fetcher.for<paths>>;
    adminFetcher: ReturnType<typeof Fetcher.for<adminPaths>>;
}

const defaultRuntimeProps : RuntimeProps = {
    AAA_URL: 'http://localhost.arxiv.org:5000/aaa',
    ADMIN_API_BACKEND_URL: 'http://localhost.arxiv.org:5000/admin-api',
    ADMIN_APP_ROOT: 'http://localhost.arxiv.org:5000/admin-console/',
    ARXIV_COOKIE_NAME: "arxiv_oidc_session",
    TAPIR_COOKIE_NAME: "tapir_session",
    ARXIV_KEYCLOAK_COOKIE_NAME: "arxiv_keycloak_token",
    ARXIV_CHECK: "https://check.dev.arxiv.org",
    URLS: arXivURLs,
    updateEnv: (key, value) => { },
    aaaFetcher: Fetcher.for<paths>(),
    adminFetcher: Fetcher.for<adminPaths>(),
};

export const RuntimeContext = createContext<RuntimeProps>(defaultRuntimeProps);

interface RuntimeContextProviderProps {
    children: React.ReactNode;
}

export const RuntimeContextProvider = ({ children } : RuntimeContextProviderProps) => {
    const [runtimeEnv, setRuntimeEnv] = useState<RuntimeProps>(defaultRuntimeProps);
    const [loading, setLoading] = useState<boolean>(true);

    const updateRuntimeEnv = (props: Partial<RuntimeProps>) => {
        const newEnv = Object.assign({}, runtimeEnv, props);
        setRuntimeEnv(newEnv);
    }

    const updateRuntimeProps = (key: string, value: string) => {
        updateRuntimeEnv({[key]: value});
    }

    useEffect(() => {
        updateRuntimeEnv({updateEnv: updateRuntimeProps});

        const fetchRuntimeEnvironment = async () => {
            try {
                let baseUrl = window.location.protocol + "//" + window.location.hostname;
                if ((window.location.port !== "80") && (window.location.port !== "") && (window.location.port !== "443"))
                    baseUrl = baseUrl + ":" + window.location.port;
                baseUrl = baseUrl + "/";
                const aaaUrl = baseUrl + "aaa";
                const adminUrl = baseUrl + "admin-api";

                const runtime1: Partial<RuntimeProps> = {
                    AAA_URL: aaaUrl,
                    ADMIN_API_BACKEND_URL: adminUrl,
                    ADMIN_APP_ROOT: baseUrl + "admin-console/",
                    ARXIV_COOKIE_NAME: defaultRuntimeProps.ARXIV_COOKIE_NAME,
                    TAPIR_COOKIE_NAME: defaultRuntimeProps.TAPIR_COOKIE_NAME,
                };
                console.log("runtime-1: " + JSON.stringify(runtime1));
                updateRuntimeEnv(runtime1);
                const cookie_name_response = await fetch(`${runtime1.AAA_URL}/token-names`);
                const cookie_names = await cookie_name_response.json();
                console.log("cookie_names: " + JSON.stringify(cookie_names));

                const aaaFetcher = Fetcher.for<paths>();
                aaaFetcher.configure({baseUrl: aaaUrl});

                const adminFetcher = Fetcher.for<paths>();
                adminFetcher.configure({baseUrl: adminUrl});

                const runtime2: Partial<RuntimeProps> = {
                    AAA_URL: aaaUrl,
                    ADMIN_API_BACKEND_URL: adminUrl,
                    ADMIN_APP_ROOT: baseUrl + "admin-console/",
                    ARXIV_COOKIE_NAME: cookie_names.session,
                    TAPIR_COOKIE_NAME: cookie_names.classic,
                    aaaFetcher: aaaFetcher,
                    adminFetcher: adminFetcher,
                };

                console.log("runtime-2: " + JSON.stringify(runtime2));
                updateRuntimeEnv(runtime2);
            } catch (error) {
                console.error('Error fetching runtime urls:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchRuntimeEnvironment().then(_r => null);
    }, []);

    useEffect(() => {
        const it = Fetcher.for<paths>();
        it.configure({baseUrl: runtimeEnv.AAA_URL});
        updateRuntimeEnv({aaaFetcher: it});
    }, [runtimeEnv.AAA_URL]);

    useEffect(() => {
        const it = Fetcher.for<adminPaths>();
        it.configure({baseUrl: runtimeEnv.ADMIN_API_BACKEND_URL});
        updateRuntimeEnv({adminFetcher: it});
    }, [runtimeEnv.ADMIN_API_BACKEND_URL]);


    if (loading) {
        return (<Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh"><CircularProgress /></Box>);
    }

    return (
        <RuntimeContext.Provider value={runtimeEnv}>
            {children}
        </RuntimeContext.Provider>
    );
};