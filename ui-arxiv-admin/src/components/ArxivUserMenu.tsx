import React, { useContext, useState } from 'react';
import { useLogout } from 'react-admin';
import {
    Box,
    Typography,
    IconButton,
    Menu,
    MenuItem,
    ListItemIcon,
    ListItemText
} from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import SettingsIcon from '@mui/icons-material/Settings';
import { RuntimeContext } from "../RuntimeContext";

export const ArxivUserMenu = () => {
    const { currentUser, currentUserLoading } = useContext(RuntimeContext);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const logout = useLogout();
    const open = Boolean(anchorEl);

    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleClose = () => {
        setAnchorEl(null);
    };

    const handleLogout = () => {
        handleClose();
        logout();
    };

    const handleUserPreferences = () => {
        handleClose();
        // TODO: Implement user preferences
        console.log('User preferences not implemented yet');
    };

    return (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {!currentUserLoading && currentUser && (
                <Typography sx={{ fontSize: "0.875rem", ml: 1, mr: 0 }}>
                    {currentUser.first_name} {currentUser.last_name}
                </Typography>
            )}
            <IconButton
                onClick={handleClick}
                size="small"
                sx={{ ml: "4px" }}
                aria-controls={open ? 'account-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={open ? 'true' : undefined}
            >
                <AccountCircleIcon />
            </IconButton>
            <Menu
                id="account-menu"
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                onClick={handleClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
                <MenuItem onClick={handleUserPreferences}>
                    <ListItemIcon>
                        <SettingsIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>User Preferences...</ListItemText>
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                    <ListItemIcon>
                        <LogoutIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Log out</ListItemText>
                </MenuItem>
            </Menu>
        </Box>
    );
};