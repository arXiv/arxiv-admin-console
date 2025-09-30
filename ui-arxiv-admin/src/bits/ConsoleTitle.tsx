import React from 'react';
import Typography from '@mui/material/Typography';

interface ConsoleTitleProps {
    children: React.ReactNode;
    sx?: object;
}

const ConsoleTitle: React.FC<ConsoleTitleProps> = ({ children, sx = {} }) => {
    return (
        <Typography
            variant="h1"
            sx={{
                mt: "3rem",
                ...sx
            }}
        >
            {children}
        </Typography>
    );
};

export default ConsoleTitle;