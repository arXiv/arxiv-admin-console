import React from 'react';
import { Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import { TitlePortal } from 'react-admin';

const TitleContainer = styled(Box)(({ theme }) => ({
    padding: theme.spacing(2, 3),
    borderBottom: `1px solid ${theme.palette.divider}`,
    backgroundColor: theme.palette.background.paper,
}));

export const TitleDisplay: React.FC = () => {
    return (
        <TitleContainer>
            <TitlePortal
                variant="h5"
                sx={{
                    fontSize: '1.25rem',
                    fontWeight: 500,
                    margin: 0,
                }}
            />
        </TitleContainer>
    );
};