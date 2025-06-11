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
    QuestionMark as SuspectIcon,
    StopCircle as OnHoldIcon
} from '@mui/icons-material';
import { useSlidingPanel } from '../SlidingPanelContext';
import {RuntimeContext} from "../RuntimeContext";
import OwnershipRequestIcon from "@mui/icons-material/Star";

interface LinkItem {
    title: string;
    url: string;
    icon?: React.ReactNode;
    description?: string;
    external?: boolean;
    action?: string; // For special actions like opening devtools
}

interface LinkPanelProps {
    onNavigate: (path: string) => void;
}

export const LinkPanel: React.FC<LinkPanelProps> = ({ onNavigate }) => {
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
            url: '/',
            icon: <DashboardIcon />,
            description: 'Admin dashboard'
        },
        {
            title: 'Jira',
            url: 'https://arxiv-org.atlassian.net/jira/servicedesk/projects/AH/issues',
            icon: <HelpIcon />,
            description: 'Jira Service Desk',
            external: true
        },
        {
            title: 'Oh Hold',
            url: '/submissions?displayedFilters=%5B%5D&filter=%7B%22submission_status%22%3A%5B2%5D%7D&order=ASC&page=1&perPage=10&sort=id',
            icon: <OnHoldIcon />,
            description: 'On Hold Submissions',
        },
        {
            title: 'Suspect',
            url: '/users?displayedFilters=%7B%22suspect%22%3Atrue%7D&filter=%7B%22suspect%22%3Atrue%7D&order=ASC&page=1&perPage=10&sort=id',
            icon: <SuspectIcon />,
            description: 'Suspected Users',
        },

        {
            title: 'Ownership Requests',
            url: '/ownership_requests?displayedFilters={}&filter={%22workflow_status%22%3A%22pending%22}&order=ASC&page=1&perPage=25&sort=id',
            icon: <OwnershipRequestIcon />,
            description: 'Pending Ownership Requests',
        },
    ];
/*

                            <Box>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"flag_edit_users":true}'}}>
                                    Administrators
                                </Button>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"flag_is_mod":true}'}}>
                                    Moderators
                                </Button>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"suspect":true}'}}>
                                    Suspect Users
                                </Button>
                            </Box>
                            <Box>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"is_non_academic":true}'}}>
                                    Non academic emails for last 90 days
                                </Button>
                            </Box>
                        </Box>
                    </CardContent>
                </Card>
            </Box>

 */

    const handleLinkClick = (item: LinkItem) => {
        if (item.external) {
            window.open(item.url, '_blank', 'noopener,noreferrer');
        } else {
            onNavigate(item.url);
        }
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
                        // zIndex: 1050, // Below appbar but above content
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
                        right: "320px", // Width of the drawer
                        bottom: 0,
                        // zIndex: 1000,
                        pointerEvents: 'none', // Allow clicks to pass through
                    }}
                />
            )}
        </>
    );
};