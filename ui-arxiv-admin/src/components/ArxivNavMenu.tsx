import React, {useState, useRef} from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import {ArxivNavLink} from "../arxivNavLinks";
import {RuntimeContext} from "../RuntimeContext";
import {useMediaQuery} from "@mui/material";
import Tooltip from "@mui/material/Tooltip";

const ArxivNavMenu = () => {
    const runtimeProps = React.useContext(RuntimeContext);
    const [anchorEls, setAnchorEls] = useState<{ [key: string]: HTMLElement | null }>({});
    const closeTimeoutsRef = useRef<{ [key: string]: NodeJS.Timeout }>({});
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('lg'));

    const handleMenuOpen = (menuId: string) => (event?: React.MouseEvent<HTMLElement>) => {
        // Clear any pending close timeout for this menu
        if (closeTimeoutsRef.current[menuId]) {
            clearTimeout(closeTimeoutsRef.current[menuId]);
            delete closeTimeoutsRef.current[menuId];
        }

        if (event) {
            setAnchorEls(prev => ({
                ...prev,
                [menuId]: event.currentTarget
            }));
        }
    };

    const handleMenuClose = (menuId: string) => () => {
        // Set a timeout before closing the menu
        const timeout = setTimeout(() => {
            setAnchorEls(prev => ({
                ...prev,
                [menuId]: null
            }));
        }, 150); // Shorter delay

        closeTimeoutsRef.current[menuId] = timeout;
    };

    const handleMenuItemClick = (url: string, app: string) => {
        if (url && app === 'external') {
            window.open(url, '_blank');
        } else if (url) {
            // Handle internal navigation if needed
            window.open(url, '_blank');
        }
        // Close all menus
        setAnchorEls({});
    };

    const flattenMenuItems = (items: ArxivNavLink[], level: number = 0): Array<{
        item: ArxivNavLink,
        level: number
    }> => {
        const result: Array<{ item: ArxivNavLink, level: number }> = [];

        items.forEach((item) => {
            result.push({item, level});

            if (item.items && item.items.length > 0) {
                result.push(...flattenMenuItems(item.items, level + 1));
            }
        });

        return result;
    };


    return (
        <Box sx={{
            '& .MuiButton-root': {
                textTransform: "none",
                margin: isSmall ? 0 : 1,
            }
        }}>
            {
                runtimeProps.arxivNavLinks.map((categorySection: ArxivNavLink) => {
                    const flattenedItems = categorySection.items ? flattenMenuItems(categorySection.items) : [];

                    return (
                        <React.Fragment key={categorySection.id}>
                            <Button
                                color="inherit"
                                onMouseEnter={handleMenuOpen(categorySection.id)}
                                onMouseLeave={handleMenuClose(categorySection.id)}
                            >
                                {categorySection.title}
                            </Button>
                            <Menu
                                anchorEl={anchorEls[categorySection.id]}
                                open={Boolean(anchorEls[categorySection.id])}
                                onClose={handleMenuClose(categorySection.id)}
                                anchorOrigin={{
                                    vertical: 'bottom',
                                    horizontal: 'left',
                                }}
                                transformOrigin={{
                                    vertical: 'top',
                                    horizontal: 'left',
                                }}
                                MenuListProps={{
                                    onMouseEnter: () => handleMenuOpen(categorySection.id)(),
                                    onMouseLeave: handleMenuClose(categorySection.id),
                                    sx: { pt: 0 }
                                }}
                                slotProps={{
                                    root: {
                                        sx: {
                                            pointerEvents: 'none',
                                        }
                                    },
                                    paper: {
                                        sx: {
                                            pointerEvents: 'auto',
                                            mt: 0
                                        }
                                    }
                                }}
                            >
                                {flattenedItems.map(({item, level}) => {
                                    const isNotApplicable = item.app === 'not_applicable';
                                    const isClickable = item.url && !isNotApplicable;
                                    const indentPx = level * 12;

                                    return (
                                        <Tooltip title={item.url}>
                                            <MenuItem
                                                key={item.id}
                                                onClick={isClickable ? () => handleMenuItemClick(item.url, item.app) : undefined}
                                                disabled={!item.active || isNotApplicable}
                                                sx={{
                                                    pl: 2 + (indentPx / 8), // Convert px to theme spacing units
                                                    color: isNotApplicable ? 'text.secondary' : 'text.primary',
                                                    fontWeight: isNotApplicable ? 'bold' : 'normal',
                                                    cursor: isClickable ? 'pointer' : 'default',
                                                    '&:hover': {
                                                        backgroundColor: isClickable ? 'action.hover' : 'transparent'
                                                    },
                                                    '&.Mui-disabled': {
                                                        color: isNotApplicable ? 'text.secondary' : 'text.disabled',
                                                        opacity: 0.8
                                                    }
                                                }}
                                            >
                                                {item.title}
                                            </MenuItem>
                                        </Tooltip>
                                    );
                                })}
                            </Menu>
                        </React.Fragment>
                    );
                })
            }
        </Box>
    )
}

export default ArxivNavMenu;
