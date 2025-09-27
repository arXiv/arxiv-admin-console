import React from 'react';
import {
    CheckForApplicationUpdate,
    Menu,
    useSidebarState
} from 'react-admin';
import { styled } from '@mui/material';
import { AdminConsoleAppBar } from '../components/AdminConsoleAppBar';
import { CollapsibleRightMenu } from '../components/CollapsibleRightMenu';
import Box from '@mui/material/Box';
import {DarkLimeColor, LightLimeColor} from "../navTheme";

// Styled components for right sidebar layout
const RightSidebarRoot = styled('div')(({ theme }) => ({
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    position: 'relative',
    backgroundColor: theme.palette.background.default,
}));

const RightSidebarFrame = styled('div')(({ theme }) => ({
    display: 'flex',
    flexDirection: 'row',
    flex: 1,
    overflow: 'hidden',
}));

const sideMargin = 8;
const showLegendWidth = 240;
const hideLegendWidth = 40;


const AdminContentRoot = styled('main', {
    shouldForwardProp: (prop) => prop !== 'open' && prop !== 'expandedWidth' && prop !== 'collapsedWidth',
})<{ open?: boolean; expandedWidth?: number; collapsedWidth?: number }>(({ theme, open, expandedWidth = showLegendWidth + sideMargin, collapsedWidth = hideLegendWidth + sideMargin }) => ({
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto',
    marginRight: open ? expandedWidth  : collapsedWidth,
    marginLeft: sideMargin,
    marginTop: theme.spacing(8), // Account for fixed AppBar height
    transition: theme.transitions.create(['margin'], {
        easing: theme.transitions.easing.easeOut,
        duration: theme.transitions.duration.enteringScreen,
    }),
}));

const RightSidebarContainer = styled('div', {
    shouldForwardProp: (prop) => prop !== 'open' && prop !== 'expandedWidth' && prop !== 'collapsedWidth',
})<{ open?: boolean; expandedWidth?: number; collapsedWidth?: number }>(({ theme, open, expandedWidth = showLegendWidth, collapsedWidth = hideLegendWidth }) => ({
    width: open ? expandedWidth : collapsedWidth,
    position: 'fixed',
    right: 0,
    top: 0,
    height: '100vh',
    zIndex: theme.zIndex.drawer - 1,
    transition: theme.transitions.create(['width'], {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    backgroundColor: theme.palette.mode === 'dark' ? DarkLimeColor : LightLimeColor,
    borderLeft: `1px solid ${theme.palette.divider}`,
    display: 'flex',
    flexDirection: 'column',
    paddingTop: theme.spacing(8), // Account for app bar height
    overflow: 'hidden',
}));

interface RightSidebarLayoutProps {
    children: React.ReactNode;
    dashboard?: React.ComponentType;
    error?: React.ComponentType<{ error?: any; errorInfo?: any }>;
    menu?: React.ComponentType;
    appBar?: React.ComponentType;
}

export const RightSidebarLayout: React.FC<RightSidebarLayoutProps> = ({
    children,
    dashboard,
    error,
    menu = CollapsibleRightMenu,
    appBar = AdminConsoleAppBar,
    ...props
}) => {
    const [open, setOpen] = useSidebarState();

    const handleDrawerToggle = () => {
        setOpen(!open);
    };

    // Create a custom app bar that includes the toggle button on the right
    const CustomAppBar = () => {
        const AppBarComponent = appBar as React.ComponentType<any>;
        return (
            <AppBarComponent
                {...props}
                onMenuClick={handleDrawerToggle}
                open={open}
            />
        );
    };

    const MenuComponent = menu as React.ComponentType<any>;

    return (
        <RightSidebarRoot>
            <CheckForApplicationUpdate />
            <CustomAppBar />
            <RightSidebarFrame>
                <AdminContentRoot open={open}>
                    {children}
                </AdminContentRoot>
                <RightSidebarContainer open={open}>
                    <MenuComponent />
                </RightSidebarContainer>
            </RightSidebarFrame>
        </RightSidebarRoot>
    );
};