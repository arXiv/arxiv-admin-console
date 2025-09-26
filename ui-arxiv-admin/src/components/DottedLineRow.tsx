import React from 'react';
import { Box, Typography } from '@mui/material';

interface DottedLineRowProps {
    label: string;
    children: React.ReactNode;
}

export const DottedLineRow: React.FC<DottedLineRowProps> = ({ label, children }) => {
    return (
        <Box display="flex" alignItems="center">
            <Typography variant="body2" sx={{ minWidth: 0, color: '#c4d82e', fontSize: '1em' }}>
                {label}
            </Typography>
            <Box sx={{
                flex: 1,
                mx: 1,
                display: 'flex',
                alignItems: 'baseline',
                '&::before': {
                    content: '""',
                    flex: 1,
                    height: '1px',
                    background: 'repeating-linear-gradient(to right, #ccc 0px, #ccc 3px, transparent 3px, transparent 8px)',
                    marginTop: '8px'
                }
            }} />
            <Box sx={{
                textAlign: 'right',
                color: '#F0F5CF',
                fontSize: '1em',
                '& *': {
                    color: '#F0F5CF !important'
                }
            }}>
                {children}
            </Box>
        </Box>
    );
};