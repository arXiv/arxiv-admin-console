import React from 'react';
import {
    useResourceDefinitions,
    useBasename,
    MenuItemLink,
    useSidebarState,
} from 'react-admin';
import {
    List,
    Tooltip,
    Box,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import DashboardIcon from '@mui/icons-material/Dashboard';
import Typography from "@mui/material/Typography";

const CollapsibleMenuContainer = styled(Box, {
    shouldForwardProp: (prop) => prop !== 'open',
})<{ open?: boolean }>(({ theme, open }) => ({
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    minHeight: 0,
    overflowX: 'hidden',
    overflowY: 'auto',
}));

const MenuList = styled(List)(({ theme }) => ({
    padding: 0,
}));

const StyledMenuItemLink = styled(MenuItemLink, {
    shouldForwardProp: (prop) => prop !== 'open',
})<{ open?: boolean }>(({ theme, open }) => ({
    minHeight: 48,
    height: 48,
    display: 'flex',
    alignItems: 'center',
    '& .MuiListItemButton-root': {
        paddingLeft: 0,
        paddingRight: 0,
        justifyContent: 'flex-start',
        minHeight: 48,
        height: 48,
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        width: '100%',
    },
    '& .MuiListItemIcon-root': {
        position: 'absolute',
        left: '8px',
        top: '50%',
        transform: 'translateY(-50%)',
        minWidth: '24px',
        height: '24px',
    },
    '& .MuiListItemText-root': {
        display: open ? 'block' : 'none',
    },
    // Target the text content directly, not the icon
    '&': {
        textIndent: '24px', // Push text content to the right
    },
    '&.RaMenuItemLink-active': {
        backgroundColor: theme.palette.action.selected,
        borderRadius: theme.shape.borderRadius,
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
                {open ? (
                    <StyledMenuItemLink
                        open={open}
                        to={`${basename}/`}
                        primaryText="Dashboard"
                        leftIcon={<DashboardIcon />}
                        onClick={handleMenuItemClick}
                    />
                ) : (
                    <Tooltip title={"Dashboard"} placement="left">
                        <StyledMenuItemLink
                            open={open}
                            to={`${basename}/`}
                            primaryText=""
                            leftIcon={<DashboardIcon />}
                            onClick={handleMenuItemClick}
                        />
                    </Tooltip>
                )}

                {/* Resource Items */}
                {Object.keys(resources)
                    .filter((name) => resources[name].hasList)
                    .map((name) => {
                        const resource = resources[name];
                        const label = resource.options?.label || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
                        return open ? (
                            <StyledMenuItemLink
                                key={name}
                                open={open}
                                to={`${basename}/${name}`}
                                primaryText={label}
                                leftIcon={resource.icon ? <resource.icon /> : undefined}
                                onClick={handleMenuItemClick}
                            />
                        ) : (
                            <Tooltip key={name} title={label} placement="left">
                                <StyledMenuItemLink
                                    open={open}
                                    to={`${basename}/${name}`}
                                    primaryText=""
                                    leftIcon={resource.icon ? <resource.icon /> : undefined}
                                    onClick={handleMenuItemClick}
                                />
                            </Tooltip>
                        );
                    })}
            </MenuList>
        </CollapsibleMenuContainer>
    );
};