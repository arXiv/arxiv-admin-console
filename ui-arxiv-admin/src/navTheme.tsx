import { createTheme } from '@mui/material/styles';
import { defaultTheme, defaultDarkTheme } from 'react-admin';

// Common typography base (sizes and font family)
const commonTypographyBase = {
    fontFamily: 'IBM Plex Mono, monospace',
    fontSize: 14,
    body1: {
        fontSize: '14px',
        lineHeight: '1em',
    },
    body2: {
        fontSize: '14px',
        lineHeight: '1em',
    },
    h1: {
        fontSize: '40px',
        fontWeight: 700,
    },
    h2: {
        fontSize: '20px',
        fontWeight: 700,
    },
    h6: {
        fontWeight: 700,
    },
};

const lightTheme = createTheme({
    ...defaultTheme,
    typography: {
        ...defaultTheme.typography,
        ...commonTypographyBase,
        body1: {
            ...commonTypographyBase.body1,
            color: '#000000',
        },
        body2: {
            ...commonTypographyBase.body2,
            color: '#000000',
        },
        h1: {
            ...commonTypographyBase.h1,
            color: '#000000',
        },
        h2: {
            ...commonTypographyBase.h2,
            color: '#6b6459', // Library Grey
        },
    },
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
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none', // Prevent uppercase transformation
                },
                contained: {
                    backgroundColor: '#C4D82E', // Access Lime
                    color: '#000000', // Black text
                    border: 'none',
                    '&:hover': {
                        backgroundColor: '#F0F5CF', // Light Lime
                        color: '#000000', // Black text (no change)
                    },
                },
                outlined: {
                    backgroundColor: '#ffffff', // White background
                    color: '#000000', // Black text
                    border: '3px solid #C4D82E', // Access Lime border
                    '&:hover': {
                        backgroundColor: '#F0F5CF', // Light Lime
                        color: '#000000', // Black text (no change)
                        border: '3px solid #C4D82E', // Same border (no change)
                    },
                },
            },
        },
        MuiSwitch: {
            styleOverrides: {
                switchBase: {
                    color: '#6b6459', // Library Grey (inactive)
                    '&.Mui-checked': {
                        color: '#1f5e96', // Archival Blue (active)
                        '& + .MuiSwitch-track': {
                            backgroundColor: '#1f5e96', // Archival Blue (active track)
                        },
                    },
                },
                track: {
                    backgroundColor: '#6b6459', // Library Grey (inactive track)
                },
            },
        },
    },
});

const darkTheme = createTheme({
    ...defaultDarkTheme,
    typography: {
        ...defaultDarkTheme.typography,
        ...commonTypographyBase,
        body1: {
            ...commonTypographyBase.body1,
            color: '#ffffff',
        },
        body2: {
            ...commonTypographyBase.body2,
            color: '#ffffff',
        },
        h1: {
            ...commonTypographyBase.h1,
            color: '#ffffff',
        },
        h2: {
            ...commonTypographyBase.h2,
            color: '#a8a19a', // Lighter Library Grey for dark theme
        },
    },
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
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none', // Prevent uppercase transformation
                },
                contained: {
                    backgroundColor: '#7A8F1A', // Darker Access Lime for dark theme
                    color: '#ffffff', // White text for dark theme
                    border: 'none',
                    '&:hover': {
                        backgroundColor: '#1B3B1B', // Very dark green for dark theme
                        color: '#ffffff', // White text (no change)
                    },
                },
                outlined: {
                    backgroundColor: '#2A2A2A', // Dark background instead of white
                    color: '#ffffff', // White text for dark theme
                    border: '3px solid #7A8F1A', // Darker Access Lime border
                    '&:hover': {
                        backgroundColor: '#1B3B1B', // Very dark green for dark theme
                        color: '#ffffff', // White text (no change)
                        border: '3px solid #7A8F1A', // Same border (no change)
                    },
                },
            },
        },
        MuiSwitch: {
            styleOverrides: {
                switchBase: {
                    color: '#6b6459', // Library Grey (inactive)
                    '&.Mui-checked': {
                        color: '#1f5e96', // Archival Blue (active)
                        '& + .MuiSwitch-track': {
                            backgroundColor: '#1f5e96', // Archival Blue (active track)
                        },
                    },
                },
                track: {
                    backgroundColor: '#6b6459', // Library Grey (inactive track)
                },
            },
        },
    },
});

export { lightTheme, darkTheme };
