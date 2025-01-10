import { createTheme } from '@mui/material/styles';
import { defaultTheme, defaultDarkTheme } from 'react-admin';

const lightTheme = createTheme({
    ...defaultTheme,
    components: {
        ...defaultTheme.components,
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: '#b31b1b', // Background color for AppBar in light theme
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
                    backgroundColor: '#b31b1b', // Background color for AppBar in dark theme
                },
            },
        },
    },
});

export { lightTheme, darkTheme };
