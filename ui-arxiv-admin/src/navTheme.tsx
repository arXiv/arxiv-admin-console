import { createTheme } from '@mui/material/styles';
import { defaultTheme, defaultDarkTheme } from 'react-admin';

export const LightLimeColor = '#F0F5CF';
export const DarkLimeColor = '#1B3B1B';
export const AccessLimeColor = '#C4D82E';
export const DarkAccessLimeColor = '#7A8F1A';
export const ArchivalBlueColor ='#1f5e96';
export const LibraryGreyColor = '#6b6459'; // for light theme
export const LighterLibraryGreyColor = '#a8a19a'; // for dark theme
export const VeryLightGreyColor = '#f0f0f0'
export const VeryVeryLightGreyColor = '#f8f8f8'
export const WHITE = '#FFFFFF';
export const BLACK = '#000000';


// Common base theme (sizes, spacing, behavior)
const commonBaseTheme = {
    typography: {
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 16,
        body1: {
            fontSize: '14px',
        },
        body2: {
            fontSize: '13px',
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
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none' as const, // Prevent uppercase transformation
                },
            },
        },
        MuiSwitch: {
            styleOverrides: {
                switchBase: {
                    // Size and behavior styles only
                },
                track: {
                    // Size and behavior styles only
                },
            },
        },
        MuiTooltip: {
            styleOverrides: {
                tooltip: {
                    fontSize: '20px !important', // Force larger font size
                    color: WHITE,
                },
            },
        },
    },
};

const lightTheme = createTheme({
    ...defaultTheme,
    ...commonBaseTheme,
    typography: {
        ...defaultTheme.typography,
        ...commonBaseTheme.typography,
        body1: {
            ...commonBaseTheme.typography.body1,
            color: BLACK,
        },
        body2: {
            ...commonBaseTheme.typography.body2,
            color: BLACK,
        },
        h1: {
            ...commonBaseTheme.typography.h1,
            color: BLACK,
        },
        h2: {
            ...commonBaseTheme.typography.h2,
            color: LibraryGreyColor,
        },
    },
    palette: {
        ...defaultTheme.palette,
        background: {
            ...defaultTheme.palette?.background,
            default: VeryLightGreyColor, // Very light grey for main content background
            paper: VeryVeryLightGreyColor, // Keep paper/card backgrounds white
        },
    },
    components: {
        ...defaultTheme.components,
        ...commonBaseTheme.components,
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
                ...commonBaseTheme.components.MuiButton.styleOverrides,
                contained: {
                    backgroundColor: AccessLimeColor, // Access Lime
                    color: BLACK, // Black text
                    border: 'none',
                    '&:hover': {
                        backgroundColor: LightLimeColor, // Light Lime
                        color: BLACK, // Black text (no change)
                    },
                },
                outlined: {
                    backgroundColor: WHITE, // White background
                    color: BLACK, // Black text
                    border: '2px solid ' + AccessLimeColor, // Access Lime border
                    '&:hover': {
                        backgroundColor: LightLimeColor, // Light Lime
                        color: BLACK, // Black text (no change)
                        border: '2px solid ' + AccessLimeColor, // Same border (no change)
                    },
                },
            },
        },
        MuiSwitch: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiSwitch.styleOverrides,
                switchBase: {
                    color: LibraryGreyColor, // Library Grey (inactive)
                    '&.Mui-checked': {
                        color: ArchivalBlueColor, // Archival Blue (active)
                        '& + .MuiSwitch-track': {
                            backgroundColor: ArchivalBlueColor, // Archival Blue (active track)
                        },
                    },
                },
                track: {
                    backgroundColor: LibraryGreyColor, // Library Grey (inactive track)
                },
            },
        },
        MuiTooltip: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiTooltip.styleOverrides,
                tooltip: {
                    color: WHITE,
                },
            },
        },
    },
});

const darkTheme = createTheme({
    ...defaultDarkTheme,
    ...commonBaseTheme,
    typography: {
        ...defaultDarkTheme.typography,
        ...commonBaseTheme.typography,
        body1: {
            ...commonBaseTheme.typography.body1,
            color: WHITE,
        },
        body2: {
            ...commonBaseTheme.typography.body2,
            color: WHITE,
        },
        h1: {
            ...commonBaseTheme.typography.h1,
            color: WHITE,
        },
        h2: {
            ...commonBaseTheme.typography.h2,
            color: LighterLibraryGreyColor, // Lighter Library Grey for dark theme
        },
    },
    components: {
        ...defaultDarkTheme.components,
        ...commonBaseTheme.components,
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
                ...commonBaseTheme.components.MuiButton.styleOverrides,
                contained: {
                    backgroundColor: DarkAccessLimeColor, // Darker Access Lime for dark theme
                    color: WHITE, // White text for dark theme
                    border: 'none',
                    '&:hover': {
                        backgroundColor: DarkLimeColor, // Very dark green for dark theme
                        color: WHITE, // White text (no change)
                    },
                },
                outlined: {
                    backgroundColor: '#2A2A2A', // Dark background instead of white
                    color: WHITE, // White text for dark theme
                    border: '2px solid ' + DarkAccessLimeColor, // Darker Access Lime border
                    '&:hover': {
                        backgroundColor: DarkLimeColor, // Very dark green for dark theme
                        color: WHITE, // White text (no change)
                        border: '2px solid ' + DarkAccessLimeColor, // Same border (no change)
                    },
                },
            },
        },
        MuiSwitch: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiSwitch.styleOverrides,
                switchBase: {
                    color: LibraryGreyColor, // Library Grey (inactive)
                    '&.Mui-checked': {
                        color: ArchivalBlueColor, // Archival Blue (active)
                        '& + .MuiSwitch-track': {
                            backgroundColor: ArchivalBlueColor, // Archival Blue (active track)
                        },
                    },
                },
                track: {
                    backgroundColor: LibraryGreyColor, // Library Grey (inactive track)
                },
            },
        },
        MuiTooltip: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiTooltip.styleOverrides,
                tooltip: {
                    color: WHITE,
                },
            },
        },
    },
});

export { lightTheme, darkTheme };
