import { createTheme } from '@mui/material/styles';
import { defaultTheme, defaultDarkTheme } from 'react-admin';

const lightTheme = createTheme({
    ...defaultTheme,
    palette: {
        ...defaultTheme.palette,
        background: {
            ...defaultTheme.palette?.background,
            default: '#f0f0f0', // Very light grey for main content background
            paper: '#f8f8f8', // Keep paper/card backgrounds white
        },
    },
    components: {
        ...defaultTheme.components,
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: '#fff', // Background color for AppBar in light theme
                    color: '#111', // Dark text for light theme
                    '& .MuiTypography-root': {
                        color: '#111',
                    },
                },
            },
        },
    },
});

const darkTheme = createTheme({
    ...defaultDarkTheme,
    components: {
        ...defaultDarkTheme.components,
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: '#303030', // Background color for AppBar in dark theme
                    color: '#eee', // Light text for dark theme
                    '& .MuiTypography-root': {
                        color: '#eee',
                    },
                },
            },
        },
    },
});

export { lightTheme, darkTheme };
