import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import { Link as LinkIcon } from '@mui/icons-material';
import { useSlidingPanel } from '../SlidingPanelContext';

export const PanelToggleButton: React.FC = () => {
    const { togglePanel, isPanelOpen } = useSlidingPanel();

    return (
        <Tooltip title={isPanelOpen ? 'Close Quick Links' : 'Open Quick Links'}>
            <IconButton
                color="inherit"
                onClick={togglePanel}
                sx={{
                    ml: 1, // Add some margin to separate from other appbar items
                }}
            >
                <LinkIcon />
            </IconButton>
        </Tooltip>
    );
};