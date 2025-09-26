import React from 'react';
import {
    useResourceDefinitions,
    useBasename,
    MenuItemLink,
    useSidebarState,
} from 'react-admin';
import {
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Tooltip,
    Box,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import DashboardIcon from '@mui/icons-material/Dashboard';

const CollapsibleMenuContainer = styled(Box, {
    shouldForwardProp: (prop) => prop !== 'open',
})<{ open?: boolean }>(({ theme, open }) => ({
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
}));

const MenuList = styled(List)(({ theme }) => ({
    padding: 0,
    '& .MuiListItem-root': {
        display: 'block',
        padding: 0,
    },
}));

const StyledMenuItemLink = styled(MenuItemLink, {
    shouldForwardProp: (prop) => prop !== 'open',
})<{ open?: boolean }>(({ theme, open }) => ({
    minHeight: 48,
    paddingLeft: open ? theme.spacing(1) : 0,
    paddingRight: open ? theme.spacing(1) : 0,
    justifyContent: open ? 'initial' : 'center',
    '& .MuiListItemButton-root': {
        paddingLeft: open ? theme.spacing(2) : 0,
        paddingRight: open ? theme.spacing(2) : 0,
        justifyContent: open ? 'initial' : 'center',
    },
    '& .MuiListItemIcon-root': {
        minWidth: open ? 56 : 'unset',
        marginRight: open ? theme.spacing(2) : 0,
        justifyContent: 'center',
    },
    '& .MuiListItemText-root': {
        display: open ? 'block' : 'none',
    },
    '&.RaMenuItemLink-active': {
        backgroundColor: theme.palette.action.selected,
        borderRadius: theme.shape.borderRadius,
        margin: theme.spacing(0.5),
    },
}));


export const CollapsibleRightMenu: React.FC = () => {
    const [open] = useSidebarState();
    const resources = useResourceDefinitions();
    const basename = useBasename();

    const handleMenuItemClick = (event: React.MouseEvent) => {
        // Don't prevent navigation, but close sidebar on small screens if needed
        // This can be customized based on screen size
    };

    return (
        <CollapsibleMenuContainer open={open}>
            <MenuList>
                {/* Dashboard Item */}
                <ListItem disablePadding>
                    {open ? (
                        <StyledMenuItemLink
                            open={open}
                            to={`${basename}/`}
                            primaryText="Dashboard"
                            leftIcon={<DashboardIcon />}
                            onClick={handleMenuItemClick}
                        />
                    ) : (
                        <Tooltip title="Dashboard" placement="left">
                            <StyledMenuItemLink
                                open={open}
                                to={`${basename}/`}
                                primaryText=""
                                leftIcon={<DashboardIcon />}
                                onClick={handleMenuItemClick}
                            />
                        </Tooltip>
                    )}
                </ListItem>

                {/* Resource Items */}
                {Object.keys(resources)
                    .filter((name) => resources[name].hasList)
                    .map((name) => {
                        const resource = resources[name];
                        const resourceLabel = resource.options?.label || name;

                        return (
                            <ListItem key={name} disablePadding>
                                {open ? (
                                    <StyledMenuItemLink
                                        open={open}
                                        to={`${basename}/${name}`}
                                        primaryText={resourceLabel}
                                        leftIcon={resource.icon ? <resource.icon /> : undefined}
                                        onClick={handleMenuItemClick}
                                    />
                                ) : (
                                    <Tooltip
                                        title={resourceLabel}
                                        placement="left"
                                    >
                                        <StyledMenuItemLink
                                            open={open}
                                            to={`${basename}/${name}`}
                                            primaryText=""
                                            leftIcon={resource.icon ? <resource.icon /> : undefined}
                                            onClick={handleMenuItemClick}
                                        />
                                    </Tooltip>
                                )}
                            </ListItem>
                        );
                    })}
            </MenuList>
        </CollapsibleMenuContainer>
    );
};