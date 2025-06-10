// components/SlidingPanel.tsx
import React, {useContext} from 'react';
import {
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
    Divider,
    IconButton,
    Box
} from '@mui/material';
import {
    Close as CloseIcon,
    Link as LinkIcon,
    Dashboard as DashboardIcon,
    Settings as SettingsIcon,
    Help as HelpIcon,
    Info as InfoIcon,
    Launch as LaunchIcon,
    Check as CheckIcon,
} from '@mui/icons-material';
import { useSlidingPanel } from '../SlidingPanelContext';
import {RuntimeContext} from "../RuntimeContext";

interface LinkItem {
    title: string;
    url: string;
    icon?: React.ReactNode;
    description?: string;
    external?: boolean;
    action?: string; // For special actions like opening devtools
}


export const SlidingPanel: React.FC = () => {
    const { isPanelOpen, closePanel } = useSlidingPanel();
    const runtimeProps = useContext(RuntimeContext);

    // Configure your links here
    const linkItems: LinkItem[] = [
        {
            title: 'arXiv Check',
            url: runtimeProps.ARXIV_CHECK,
            icon: <CheckIcon />,
            description: 'arXiv Check',
            external: true,
        },
        {
            title: 'Dashboard',
            url: '/admin-console/#/',
            icon: <DashboardIcon />,
            description: 'Admin dashboard'
        },
        {
            title: 'Jira',
            url: 'https://your-docs-url.com',
            icon: <HelpIcon />,
            description: 'System documentation',
            external: true
        },
        {
            title: 'Settings',
            url: '/#/settings',
            icon: <SettingsIcon />,
            description: 'Application settings'
        },
        {
            title: 'Support',
            url: 'https://your-support-url.com',
            icon: <InfoIcon />,
            description: 'Get help and support',
            external: true
        }
    ];


    const handleLinkClick = (item: LinkItem) => {
        if (item.external) {
            window.open(item.url, '_blank', 'noopener,noreferrer');
        } else {
            window.location.href = item.url;
        }
        // Don't close panel for persistent drawer
        // closePanel();
    };

    return (
        <>
            {/* Persistent Drawer */}
            <Drawer
                anchor="right"
                open={isPanelOpen}
                variant="persistent"
                sx={{
                    width: isPanelOpen ? 320 : 0,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: 320,
                        boxSizing: 'border-box',
                        // Position the drawer below the appbar
                        top: 64, // Standard React Admin appbar height
                        height: 'calc(100vh - 64px)', // Full height minus appbar
                        borderLeft: '1px solid rgba(0, 0, 0, 0.12)', // Add border for separation
                        zIndex: 1050, // Below appbar but above content
                    },
                }}
            >
                <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="h6" component="h2">
                        Quick Links
                    </Typography>
                    <IconButton onClick={closePanel} size="small">
                        <CloseIcon />
                    </IconButton>
                </Box>

                <Divider />

                <List>
                    {linkItems.map((item, index) => (
                        <ListItem key={index} disablePadding>
                            <ListItemButton onClick={() => handleLinkClick(item)}>
                                <ListItemIcon>
                                    {item.icon || <LinkIcon />}
                                </ListItemIcon>
                                <ListItemText
                                    primary={
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            {item.title}
                                            {item.external && <LaunchIcon fontSize="small" />}
                                        </Box>
                                    }
                                    secondary={item.description}
                                />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Drawer>

            {/* Content Shifter - This pushes the main content when drawer is open */}
            {isPanelOpen && (
                <Box
                    sx={{
                        position: 'fixed',
                        top: 64,
                        left: 0,
                        right: 320, // Width of the drawer
                        bottom: 0,
                        zIndex: 1000,
                        pointerEvents: 'none', // Allow clicks to pass through
                    }}
                />
            )}
        </>
    );
};
