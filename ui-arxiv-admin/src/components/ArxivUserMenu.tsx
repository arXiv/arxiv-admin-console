import React, { useState, useEffect, useContext } from 'react';
import { UserMenu, UserMenuProps } from 'react-admin';
import { Box, Typography } from '@mui/material';
import { RuntimeContext } from "../RuntimeContext";
import {paths as aaaApi} from "../types/aaa-api";

type UserType = aaaApi['/account/current']['get']['responses']['200']['content']['application/json'];

export const ArxivUserMenu = (props: UserMenuProps) => {
    const [currentUser, setCurrentUser] = useState<UserType | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const runtimeProps = useContext(RuntimeContext);

    const fetchCurrentUser = async () => {
        try {
            const getCurrentUserFetch = runtimeProps.aaaFetcher.path('/account/current').method('get').create();
            const response = await getCurrentUserFetch({});
            
            if (response.ok) {
                setCurrentUser(response.data);
            } else {
                setCurrentUser(null);
            }
        } catch (error) {
            console.error('Error fetching current user:', error);
            setCurrentUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCurrentUser();
    }, []);

    return (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {!isLoading && currentUser && (
                <Typography sx={{ fontSize: "0.875rem", mr: 1 }}>
                    {currentUser.first_name} {currentUser.last_name}
                </Typography>
            )}
            <UserMenu {...props} />
        </Box>
    );
};