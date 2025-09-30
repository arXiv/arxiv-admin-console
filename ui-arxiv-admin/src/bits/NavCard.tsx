import React from 'react';
import {
    Paper,
    Typography,
    List,
    ListItem,
    ListItemText,
    ListSubheader,
    Box,
    Link,
    Collapse
} from '@mui/material';
import { ArxivNavLink } from '../arxivNavLinks';
import LaunchIcon from '@mui/icons-material/Launch';

// Color scheme dictionary based on purpose
const purposeColorSchemes = {
    students: {
        backgroundColor: 'grey.600',
        color: 'text.contrastText',
    },
    // Add more purpose-based color schemes here as needed
    // moderator: {
    //     backgroundColor: 'warning.main',
    //     color: 'warning.contrastText',
    // },
};

// Default color scheme
const defaultColorScheme = {
    backgroundColor: 'background.paper',
    color: 'text.primary',
};

interface NavCardProps {
    navSection: ArxivNavLink;
}

const NavCard: React.FC<NavCardProps> = ({ navSection }) => {
    // Get color scheme based on purpose
    const colorScheme = navSection.purpose && purposeColorSchemes[navSection.purpose as keyof typeof purposeColorSchemes]
        ? purposeColorSchemes[navSection.purpose as keyof typeof purposeColorSchemes]
        : defaultColorScheme;

    // Debug logging
    console.log('NavCard:', {
        title: navSection.title,
        purpose: navSection.purpose,
        colorScheme: colorScheme,
        hasMatchingScheme: !!(navSection.purpose && purposeColorSchemes[navSection.purpose as keyof typeof purposeColorSchemes])
    });

    const handleLinkClick = (url: string) => {
        if (url) {
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    };

    const renderNavItem = (item: ArxivNavLink, level: number = 0) => {
        const hasSubItems = item.items && item.items.length > 0;
        const hasUrl = item.url && item.url.trim() !== '';

        if (hasSubItems) {
            // Render as a subheader with nested items
            return (
                <React.Fragment key={item.id}>
                    <ListSubheader
                        component="div"
                        sx={{
                            fontWeight: 600,
                            lineHeight: 1.2,
                            py: 1,
                            px: level * 2,
                            backgroundColor: 'transparent',
                            color: 'inherit',
                        }}
                    >
                        {item.title}
                    </ListSubheader>
                    {item.items?.map(subItem => renderNavItem(subItem, level + 1))}
                </React.Fragment>
            );
        } else if (hasUrl) {
            // Render as a clickable link
            return (
                <ListItem
                    key={item.id}
                    sx={{
                        pl: level * 2,
                        py: 0.5,
                    }}
                >
                    <ListItemText
                        primary={
                            <Box display="flex" alignItems="center" gap={1}>
                                <Link
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    sx={{
                                        fontSize: '1rem',
                                        color: 'inherit',
                                        textDecoration: 'none',
                                        '&:hover': {
                                            textDecoration: 'underline'
                                        }
                                    }}
                                >
                                    {item.title}
                                </Link>
                            </Box>
                        }
                    />
                </ListItem>
            );
        } else {
            // Render as a plain text item
            return (
                <ListItem key={item.id} sx={{ pl: level * 2 + 2, py: 0.5 }}>
                    <ListItemText
                        primary={
                            <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'inherit' }}>
                                {item.title}
                            </Typography>
                        }
                    />
                </ListItem>
            );
        }
    };

    return (
        <Paper
            elevation={2}
            sx={{
                p: 3,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'box-shadow 0.2s ease-in-out',
                borderRadius: '12px',
                backgroundColor: colorScheme.backgroundColor,
                color: colorScheme.color,
                '&:hover': {
                    boxShadow: 4
                }
            }}
        >
            {/* Card Header */}
            <Box
                sx={{
                    p: 2,
                }}
            >
                <Typography
                    variant="h6"
                    component="h2"
                    sx={{
                        fontSize: '1.5em',
                        fontWeight: 600,
                        margin: 0,
                        textAlign: 'center'
                    }}
                >
                    {navSection.title}
                </Typography>
            </Box>

            {/* Card Content */}
            <Box sx={{ flex: 1, overflow: 'auto' }}>
                <List dense disablePadding>
                    {navSection.items?.map(item => renderNavItem(item))}
                </List>
            </Box>
        </Paper>
    );
};

export default NavCard;