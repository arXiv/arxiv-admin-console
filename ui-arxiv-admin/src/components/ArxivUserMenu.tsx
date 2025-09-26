import React, { useContext } from 'react';
import { UserMenu, UserMenuProps } from 'react-admin';
import { Box, Typography } from '@mui/material';
import { RuntimeContext } from "../RuntimeContext";

export const ArxivUserMenu = (props: UserMenuProps) => {
    const { currentUser, currentUserLoading } = useContext(RuntimeContext);

    return (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {!currentUserLoading && currentUser && (
                <Typography sx={{ fontSize: "0.875rem", mr: 1 }}>
                    {currentUser.first_name} {currentUser.last_name}
                </Typography>
            )}
            <UserMenu {...props} />
        </Box>
    );
};