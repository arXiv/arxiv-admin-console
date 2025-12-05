import React, { createContext, useState, useEffect } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import {Box} from '@mui/material';
import {paths} from "./types/aaa-api";
import {paths as adminPaths,} from "./types/admin-api";
import {paths as modapiPaths, components as modapiComponents} from "./types/mod-api";
import { Fetcher } from 'openapi-typescript-fetch';
import {defaultArxivNavLinks, ArxivNavLink } from "./arxivNavLinks";

type UserType = paths['/account/current']['get']['responses']['200']['content']['application/json'];

type SharedNavSection = modapiComponents['schemas']['SharedNavSection'];

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
    KEYCLOAK_ACCESS_TOKEN_NAME: string;
    KEYCLOAK_REFRESH_TOKEN_NAME: string;
    ARXIV_CHECK: string;
    URLS: ArxiURLs;
    MODAPI_URL: string;
    currentUser: UserType | null;
    currentUserLoading: boolean;
    updateEnv: (key: string, value: string) => void;
    aaaFetcher: ReturnType<typeof Fetcher.for<paths>>;
    adminFetcher: ReturnType<typeof Fetcher.for<adminPaths>>;
    modapiFetcher?: ReturnType<typeof Fetcher.for<modapiPaths>>;
    arxivNavLinks: ArxivNavLink[];
}

const defaultRuntimeProps : RuntimeProps = {
    AAA_URL: '',
    ADMIN_API_BACKEND_URL: 'http://localhost.arxiv.org:5100/admin-api',
    ADMIN_APP_ROOT: 'http://localhost.arxiv.org:5000/admin-console/',
    ARXIV_COOKIE_NAME: "ARXIVNG_SESSION_ID",
    TAPIR_COOKIE_NAME: "tapir_session",
    KEYCLOAK_ACCESS_TOKEN_NAME: "keycloak_access_token",
    KEYCLOAK_REFRESH_TOKEN_NAME: "keycloak_refresh_token",
    ARXIV_CHECK: "https://check.dev.arxiv.org",
    URLS: arXivURLs,
    MODAPI_URL: '',
    currentUser: null,
    currentUserLoading: true,
    updateEnv: (_key, _value) => { },
    aaaFetcher: Fetcher.for<paths>(),
    adminFetcher: Fetcher.for<paths>(),
    arxivNavLinks: defaultArxivNavLinks,
};

export const RuntimeContext = createContext<RuntimeProps>(defaultRuntimeProps);

interface RuntimeContextProviderProps {
    children: React.ReactNode;
}

function toNavLinks(navs: SharedNavSection[]): ArxivNavLink[] {
    return navs.map((nav, navIndex) => {
        const sectionId = `section-${navIndex}`;

        const items: ArxivNavLink[] = nav.items
            .map((item, itemIndex): ArxivNavLink | null => {
                // Check if it's a subsection (has 'links' property)
                if ('links' in item) {
                    const subsection = item as modapiComponents['schemas']['SharedNavSubsection'];
                    return {
                        id: `${sectionId}-subsection-${itemIndex}`,
                        title: subsection.title,
                        url: '#', // Subsections don't have URLs
                        app: '',
                        active: false,
                        icon: null,
                        items: subsection.links.map((link, linkIndex): ArxivNavLink => ({
                            id: `${sectionId}-subsection-${itemIndex}-link-${linkIndex}`,
                            title: link.title,
                            url: link.url,
                            app: link.app,
                            active: false,
                            icon: null,
                        }))
                    } as ArxivNavLink;
                }
                // Otherwise it's a link (has 'url' property)
                else if ('url' in item) {
                    const link = item as modapiComponents['schemas']['SharedNavLink'];
                    return {
                        id: `${sectionId}-link-${itemIndex}`,
                        title: link.title,
                        url: link.url,
                        app: link.app,
                        active: false,
                        icon: null,
                    } as ArxivNavLink;
                }
                // Fallback if neither type matches
                return null;
            })
            .filter((item): item is ArxivNavLink => item !== null);

        return {
            id: sectionId,
            title: nav.title,
            url: '#',
            app: '',
            active: false,
            icon: null,
            items: items,
        } as ArxivNavLink;
    });
}

export const RuntimeContextProvider = ({ children } : RuntimeContextProviderProps) => {
    const [runtimeEnv, setRuntimeEnv] = useState<RuntimeProps>(defaultRuntimeProps);
    const [loading, setLoading] = useState<boolean>(true);

    const updateRuntimeEnv = (props: Partial<RuntimeProps>) => {
        const newEnv = Object.assign({}, runtimeEnv, props);
        console.debug("updateRuntimeEnv " + JSON.stringify(props));
        console.debug("aaa url -> " + runtimeEnv.AAA_URL + " ->" + newEnv.AAA_URL );
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

                const aaaFetcher = Fetcher.for<paths>();
                aaaFetcher.configure({baseUrl: aaaUrl});

                const adminFetcher = Fetcher.for<adminPaths>();
                adminFetcher.configure({baseUrl: adminUrl});

                const runtime2: Partial<RuntimeProps> = {
                    AAA_URL: aaaUrl,
                    ADMIN_API_BACKEND_URL: adminUrl,
                    ADMIN_APP_ROOT: baseUrl + "admin-console/",
                    aaaFetcher: aaaFetcher,
                    adminFetcher: adminFetcher,
                };

                console.log("runtime-2: " + JSON.stringify(runtime2));
                updateRuntimeEnv(runtime2);

                try {
                    const cookie_name_response = await fetch(`${runtime1.AAA_URL}/token-names`);
                    const cookie_names = await cookie_name_response.json();
                    console.log("cookie_names: " + JSON.stringify(cookie_names));

                    const runtime3: Partial<RuntimeProps> = {
                        ARXIV_COOKIE_NAME: cookie_names.session,
                        TAPIR_COOKIE_NAME: cookie_names.classic,
                        KEYCLOAK_ACCESS_TOKEN_NAME: cookie_names.keycloak_access,
                        KEYCLOAK_REFRESH_TOKEN_NAME: cookie_names.keycloak_refresh,
                    };
                    console.log("runtime-3: " + JSON.stringify(runtime3));
                    updateRuntimeEnv(runtime3);
                }
                catch (error) {
                    console.error('Error fetching runtime3 - cookie names:', error);
                }

            } catch (error) {
                console.error('Error fetching runtime urls:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchRuntimeEnvironment().then(_r => null);
    }, []);

    useEffect(() => {
        const fetchUserData = async () => {
            if (!runtimeEnv.AAA_URL) {
                console.log("aaaFetcher: IS GONE");
                return;
            }

            const it = Fetcher.for<paths>();
            it.configure({baseUrl: runtimeEnv.AAA_URL});
            updateRuntimeEnv({aaaFetcher: it});
            console.log(`aaaFetcher: AAA_URL ${runtimeEnv.AAA_URL}` );

            try {
                console.log("1. fetching current user");
                const getCurrentUserFetch = it.path('/account/current').method('get').create();
                const userResponse = await getCurrentUserFetch({});

                if (userResponse.ok) {
                    console.log("1. fetching current user - ok");

                    updateRuntimeEnv({
                        currentUser: userResponse.data,
                        currentUserLoading: false
                    });
                } else {
                    console.log("1. fetching current user - not ok");

                    updateRuntimeEnv({
                        currentUser: null,
                        currentUserLoading: false
                    });
                }
            } catch (userError) {
                console.error('Error fetching current user:', userError);
                updateRuntimeEnv({
                    currentUser: null,
                    currentUserLoading: false
                });
            }
        };

        fetchUserData();
    }, [runtimeEnv.AAA_URL]);

/*
    useEffect(() => {
        const it = Fetcher.for<adminPaths>();
        it.configure({baseUrl: runtimeEnv.ADMIN_API_BACKEND_URL});
        updateRuntimeEnv({adminFetcher: it});
    }, [runtimeEnv.ADMIN_API_BACKEND_URL]);
 */

/*
    useEffect(() => {
        console.log("current user " + JSON.stringify(runtimeEnv.currentUser));
    }, [runtimeEnv.currentUser]);
*/

    useEffect(() => {
        const fetchServiceInfo = async () => {
            if (runtimeEnv.adminFetcher === undefined)
                return;

            if (runtimeEnv.MODAPI_URL)
                return;

            const servicesInfoFetcher = runtimeEnv.adminFetcher.path('/system/service-info').method('get').create();
            try {
                const sinfoResponse = await servicesInfoFetcher({});
                if (sinfoResponse.ok) {
                    const serviceInfo = sinfoResponse.data;
                    const modapiFetcher = Fetcher.for<paths>();
                    modapiFetcher.configure({baseUrl: serviceInfo.modapi});
                    console.log("serviceInfo:", serviceInfo);
                    updateRuntimeEnv({MODAPI_URL: serviceInfo.modapi, modapiFetcher: modapiFetcher});
                } else {
                    console.error('Error fetching service info :', sinfoResponse);
                }
            }
            catch (error) {
                console.error('Error in fetchServiceInfo:', error);
            }
        }

        fetchServiceInfo();
    }, [runtimeEnv.adminFetcher, runtimeEnv.MODAPI_URL])


    useEffect(() => {
        const fetchNavigation = async () => {
            if (!runtimeEnv.MODAPI_URL)
                return;
            if (!runtimeEnv.ARXIV_COOKIE_NAME) {
                return;
            }

            console.log("modapi");

            // const sharedNavFetcher = runtimeEnv.modapiFetcher.path('/admin/shared_nav_header').method('get').create();
            try {
                const arxivToken = localStorage.getItem('access_token');

                const sharedNavResponse = await fetch(runtimeEnv.MODAPI_URL + '/admin/shared_nav_header',
                    {
                        headers:
                            {
                                authorization: `Bearer ${arxivToken}`,
                            },
                    });
                if (sharedNavResponse.ok) {
                    const navData = await sharedNavResponse.json();
                    console.log("shared_nav_data", navData);
                    updateRuntimeEnv({arxivNavLinks: toNavLinks(navData)});
                } else {
                    console.error('Error fetching navigation urls:', sharedNavResponse);
                }
            }
            catch (error) {

            }
        }

        fetchNavigation();
    }, [runtimeEnv.MODAPI_URL, runtimeEnv.ARXIV_COOKIE_NAME]);

    if (loading) {
        return (<Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh"><CircularProgress /></Box>);
    }

    return (
        <RuntimeContext.Provider value={runtimeEnv}>
            {children}
        </RuntimeContext.Provider>
    );
};