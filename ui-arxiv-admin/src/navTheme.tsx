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
                    backgroundColor: '#e7e7e7', // Background color for AppBar in light theme
                    color: '#222', // White text for grey background
                    '& .MuiTypography-root': {
                        color: '#222',
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
                    backgroundColor: '#282828', // Background color for AppBar in dark theme
                    color: '#fff', // White text for grey background
                    '& .MuiTypography-root': {
                        color: '#fff',
                    },
                },
            },
        },
    },
});

export { lightTheme, darkTheme };
