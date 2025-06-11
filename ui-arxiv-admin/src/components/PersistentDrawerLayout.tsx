import React, { ReactNode } from 'react';
import { Box } from '@mui/material';
import { useSlidingPanel } from '../SlidingPanelContext';

interface PersistentDrawerLayoutProps {
    children: ReactNode;
    panel?: React.ReactNode;
}


export const PersistentDrawerLayout: React.FC<PersistentDrawerLayoutProps> = ({ children, panel }) => {
    const { isPanelOpen } = useSlidingPanel();

    return (
        <Box
            sx={{
                display: 'flex',
                minHeight: '100vh',
            }}
        >
            {/* Main content area that shifts when drawer is open */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    transition: 'margin 0.3s ease',
                    marginRight: isPanelOpen ? '320px' : '0px', // Push content left when drawer opens
                    width: isPanelOpen ? 'calc(100vw - 320px)' : '100%',
                    overflow: 'hidden', // Prevent horizontal scroll
                }}
            >
                {children}
                {panel}
            </Box>
        </Box>
    );
};