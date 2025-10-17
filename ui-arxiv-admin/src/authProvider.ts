import { AuthProvider } from 'react-admin';
// import {useEffect, useState, useContext} from "react";
import {RuntimeProps} from "./RuntimeContext";
// import {getRemainingTimeInSeconds} from "./helpers/timeDiff";

function getCookie(name: string): string | null {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    if (!match) return null;

    const rawValue = decodeURIComponent(match[1].replace(/^"|"$/g, ''));
    return rawValue.replace(/\\(\d{3})/g, (_m, oct) => String.fromCharCode(parseInt(oct, 8)));
}

/*
function getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()!.split(';').shift()!.replace(/\\(\d{3})/g, (_match, octalCode) => String.fromCharCode(parseInt(octalCode, 8)))!;
    return null;
}
 */

const retryFetch = async (url: string, options: RequestInit, retries = 3, backoff = 1000): Promise<Response> => {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, options);

            if (response.ok) {
                return response;
            }
            return Promise.reject(response);
        } catch (error) {
            console.warn(`auth: Attempt ${i + 1} failed:`, error);

            if (i < retries - 1) {
                await new Promise(resolve => setTimeout(resolve, backoff));
            }
        }
    }

    console.error('auth: retries all failed. Bug? oauth2-authenticator dead?');
    return Promise.reject(new Error('NetworkError: Failed to fetch after multiple attempts.'));
};


let logoutInProgress = false;

export const createAuthProvider = (runtimeProps: RuntimeProps): AuthProvider => ({

    // called when the user attempts to log in
    login: () => {
        const currentUrl = window.location.href;
        window.location.href = `${runtimeProps.AAA_URL}/login?next_page=${encodeURIComponent(currentUrl)}`;
        return Promise.resolve();
    },

    // called when the user clicks on the logout button
    logout: () => {
        if (logoutInProgress) {
            console.log("auth: /logout in progress");
            return Promise.resolve();
        }
        logoutInProgress = true;
        console.log("auth: /logout started");

        return retryFetch(`${runtimeProps.AAA_URL}/logout?next_page=/`, {
            method: 'GET',
            credentials: 'include',
        }).then(() => {
            console.log("auth: logout fetch success");
            window.location.href = '/'; // Redirect to login page
        }).finally(() => {
            logoutInProgress = false;
        });
    },

    // called when the API returns an error
    checkError: async ({ status }: { status: number }) => {
        if (status === 401) {
            console.log("auth: checkError - token expired.");
            const token = getCookie(runtimeProps.ARXIV_COOKIE_NAME);

            if (token) {
                console.log("auth: checkError - old token exist, attempt refresh");
                try {
                    const refreshResponse = await retryFetch(`${runtimeProps.AAA_URL}/refresh`, {
                        method: 'GET',
                        credentials: 'include',
                    });

                    if (refreshResponse.ok) {
                        console.log("auth: Token refreshed successfully");
                        // Token refreshed successfully, retry the original request if needed
                        return Promise.resolve();
                    }
                } catch (error) {
                    console.error("auth: Error during token refresh", error);
                    // Handle fetch failure, logout the user
                    // await fetch(`${runtimeProps.AAA_URL}/logout`, { method: 'GET', credentials: 'include' });
                }
            }
            return Promise.reject();
        }
        else if (status === 403) {
            console.log("auth: checkError 403");
            // await fetch(`${runtimeProps.AAA_URL}/logout`, {method: 'GET', credentials: 'include'});
            return Promise.reject();
        }
        else if (status === undefined) {
            console.log("auth: checkError undefined");
            // await fetch(`${runtimeProps.AAA_URL}/logout`, {method: 'GET', credentials: 'include'});
            return Promise.resolve();
        }
        console.log(`auth: good - checkError status=${status} `);
        return Promise.resolve();
    },

    // called when the user navigates to a new location, to check for authentication
    checkAuth: async () => {
        if ((!runtimeProps.KEYCLOAK_ACCESS_TOKEN_NAME) || (!runtimeProps.ARXIV_COOKIE_NAME)) {
            return Promise.resolve();
        }

        if (runtimeProps.KEYCLOAK_ACCESS_TOKEN_NAME) {
            const kc_access_token = getCookie(runtimeProps.KEYCLOAK_ACCESS_TOKEN_NAME);
            // Store the token in local storage
            if (kc_access_token) {
                localStorage.setItem('keycloak_access_token', kc_access_token);
            }
        }

        if (runtimeProps.KEYCLOAK_REFRESH_TOKEN_NAME) {
            const kc_refresh_token = getCookie(runtimeProps.KEYCLOAK_REFRESH_TOKEN_NAME);
            if (kc_refresh_token) {
                localStorage.setItem('keycloak_refresh_token', kc_refresh_token);
            }
        }

        // store the user claims (now it is also NG cookie) as access token
        // Since cookie has it, this isn't necessary but random API may want to use the authorization header.
        // retryHttpClient uses access_token from local storage in authorization header. (I hope I don't regret
        // this)
        if (runtimeProps.ARXIV_COOKIE_NAME) {
            const arxiv_token = getCookie(runtimeProps.ARXIV_COOKIE_NAME);
            if (arxiv_token) {
                localStorage.setItem('access_token', arxiv_token);
            }
            return Promise.resolve();
        }

        console.log(JSON.stringify(document.cookie));
        return Promise.reject();
    },

    // called when the user navigates to a new location, to check for permissions / roles
    getPermissions: async () => Promise.resolve(),
});
