import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import IconButton from "@mui/material/IconButton";
import React, { useState, useEffect, useContext } from "react";
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { RuntimeContext } from "../RuntimeContext";

import {paths as aaaApi} from "../types/aaa-api";
type UserType = aaaApi['/account/current']['get']['responses']['200']['content']['application/json'];


const GlobalAppBar = () => {
    const [currentUser, setCurrentUser] = useState<UserType | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const runtimeProps = useContext(RuntimeContext);
    
    const open = Boolean(anchorEl);

    const fetchCurrentUser = async () => {
        try {
            // Use the typed OpenAPI client to get current user info
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

    const handleLogin = () => {
        window.location.href = `${runtimeProps.AAA_URL}/login?next=${window.location.href}`;
    };

    const handleLogout = async () => {
        try {
            // Use the typed OpenAPI client to logout
            const logoutFetch = runtimeProps.aaaFetcher.path('/logout').method('post').create();
            await logoutFetch({});
            setCurrentUser(null);
            setAnchorEl(null); // Close menu
            window.location.reload();
        } catch (error) {
            console.error('Error logging out:', error);
        }
    };

    const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleLoginClick = () => {
        setAnchorEl(null); // Close menu
        handleLogin();
    };

    useEffect(() => {
        fetchCurrentUser();
    }, []);

    return (
        <AppBar position="fixed" sx={{ height: "32px", zIndex: 1400, background: "#0000FF" }}>
            <Box
                display="flex"
                flexDirection="row"
                sx={{
                    color: "white",
                    height: "40px",
                    zIndex: 1400,
                    background: "#808080",
                    alignItems: "center",
                    justifyContent: "space-between",
                    paddingLeft: "10px",
                    paddingRight: "10px",
                    gap: "32px"
                }}
            >
                <Button sx={{color: "white", textTransform: "none"}}>
                    Resources
                </Button>
                <Button sx={{color: "white", textTransform: "none"}}>
                    Submission
                </Button>
                <Button sx={{color: "white", textTransform: "none"}}>
                    User Support
                </Button>
                <Button sx={{color: "white", textTransform: "none"}}>
                    Students
                </Button>
                <Box flexGrow={1} />
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    {!isLoading && currentUser && (
                        <Typography sx={{ color: "white", fontSize: "0.875rem" }}>
                            {currentUser.first_name} {currentUser.last_name}
                        </Typography>
                    )}
                    <IconButton
                        onClick={handleMenuClick}
                        sx={{ color: "white" }}
                        disabled={isLoading}
                    >
                        <AccountCircleIcon />
                    </IconButton>
                    <Menu
                        anchorEl={anchorEl}
                        open={open}
                        onClose={handleMenuClose}
                        anchorOrigin={{
                            vertical: 'bottom',
                            horizontal: 'right',
                        }}
                        transformOrigin={{
                            vertical: 'top',
                            horizontal: 'right',
                        }}
                    >
                        {currentUser ? (
                            <MenuItem onClick={handleLogout}>
                                <LogoutIcon sx={{ mr: 1 }} />
                                Logout
                            </MenuItem>
                        ) : (
                            <MenuItem onClick={handleLoginClick}>
                                <LoginIcon sx={{ mr: 1 }} />
                                Login
                            </MenuItem>
                        )}
                    </Menu>
                </Box>
            </Box>
        </AppBar>
    )
}

export default GlobalAppBar;
