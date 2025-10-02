import { createTheme } from '@mui/material/styles';
import { defaultTheme, defaultDarkTheme } from 'react-admin';

export const AdminConsoleBackgroundColor = '#F9F7F7';
export const AdminConsoleBackgroundColor2 = '#EAE8E8';

export const LightLimeColor = '#F0F5CF';
export const DarkLimeColor = '#1B3B1B';
export const AccessLimeColor = '#C4D82E';
export const DarkAccessLimeColor = '#7A8F1A';
export const ArchivalBlueColor ='#1f5e96';
export const ArchivalLightBlueColor ='#3091e6';
export const LibraryGreyColor = '#6b6459'; // for light theme
export const LighterLibraryGreyColor = '#a8a19a'; // for dark theme
export const VeryLightGreyColor = AdminConsoleBackgroundColor2
export const VeryVeryLightGreyColor = AdminConsoleBackgroundColor
export const WHITE = '#FFFFFF';
export const BLACK = '#000000';


// Common base theme (sizes, spacing, behavior)
const commonBaseTheme = {
    typography: {
        fontFamily: '"IBM Plex Sans Condensed", sans-serif', // Primary font
        fontSize: 16,
        body1: {
            fontSize: '12px',
        },
        body2: {
            fontSize: '11px',
        },
        h1: {
            fontSize: '40px',
            fontWeight: 700,
        },
        h2: {
            fontSize: '24px',
            fontWeight: 700,
        },
        h3: {
            fontSize: '22px',
            fontWeight: 700,
        },
        h4: {
            fontSize: '20px',
            fontWeight: 700,
        },
        h5: {
            fontSize: '18px',
            fontWeight: 700,
        },
        h6: {
            fontSize: '16px',
            fontWeight: 700,
        },
        // Custom variant for monospace content (System Data, code, etc.)
        monospace: {
            fontFamily: '"IBM Plex Mono", monospace', // Tertiary font
            fontSize: '13px',
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
                root: {
                    width: 36,
                    height: 22,
                    padding: 0,
                    marginRight: 8,
                    '& .MuiSwitch-switchBase': {
                        padding: 0,
                        margin: 2,
                        transitionDuration: '300ms',
                        color: '#888',
                        '&.Mui-checked': {
                            transform: 'translateX(14px)',
                            color: '#fff',
                            '& + .MuiSwitch-track': {
                                opacity: 1,
                                border: 0,
                            },
                            '&.Mui-disabled + .MuiSwitch-track': {
                                opacity: 0.5,
                            },
                        },
                        '&.Mui-focusVisible .MuiSwitch-thumb': {
                            color: AccessLimeColor,
                            border: '6px solid #fff',
                        },
                        '&.Mui-disabled .MuiSwitch-thumb': {
                            color: LibraryGreyColor,
                        },
                        '&.Mui-disabled + .MuiSwitch-track': {
                            opacity: 0.7,
                        },
                    },
                    '& .MuiSwitch-thumb': {
                        boxSizing: 'border-box',
                        width: 18,
                        height: 18,
                    },
                    '& .MuiSwitch-track': {
                        borderRadius: 22 / 2,
                        backgroundColor: '#f0f0f0',
                        border: '1px solid #888',
                        opacity: 1,
                        transition: 'background-color 300ms, border-color 300ms',
                    },
                },
            },
        },
        MuiTooltip: {
            styleOverrides: {
                tooltip: {
                    fontSize: '1rem !important', // Force larger font size
                    color: WHITE,
                },
            },
        },
        MuiTableCell: {
            styleOverrides: {
                head: {
                    fontWeight: 700,
                },
            },
        },
        MuiDivider: {
            styleOverrides: {
                root: {
                    borderBottomWidth: 2,
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
                root: {
                    ...commonBaseTheme.components.MuiSwitch.styleOverrides.root,
                    '& .MuiSwitch-switchBase': {
                        ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase'],
                        '&.Mui-checked': {
                            ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase']['&.Mui-checked'],
                            '& + .MuiSwitch-track': {
                                ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase']['&.Mui-checked']['& + .MuiSwitch-track'],
                                backgroundColor: ArchivalBlueColor,
                            },
                        },
                        '&.Mui-focusVisible .MuiSwitch-thumb': {
                            ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase']['&.Mui-focusVisible .MuiSwitch-thumb'],
                            color: ArchivalBlueColor,
                        },
                    },
                },
            },
        },
        MuiTooltip: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiTooltip.styleOverrides,
                tooltip: {
                    ...commonBaseTheme.components.MuiTooltip.styleOverrides.tooltip,
                    color: WHITE,
                },
            },
        },
        MuiDivider: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiDivider?.styleOverrides,
                root: {
                    ...commonBaseTheme.components.MuiDivider?.styleOverrides?.root,
                    borderColor: '#6b6459', // Darker for light theme
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
                root: {
                    ...commonBaseTheme.components.MuiSwitch.styleOverrides.root,
                    '& .MuiSwitch-switchBase': {
                        ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase'],
                        '&.Mui-checked': {
                            ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase']['&.Mui-checked'],
                            '& + .MuiSwitch-track': {
                                ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase']['&.Mui-checked']['& + .MuiSwitch-track'],
                                backgroundColor: ArchivalLightBlueColor,
                            },
                        },
                        '&.Mui-focusVisible .MuiSwitch-thumb': {
                            ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-switchBase']['&.Mui-focusVisible .MuiSwitch-thumb'],
                            color: ArchivalLightBlueColor,
                        },
                    },
                    '& .MuiSwitch-track': {
                        ...commonBaseTheme.components.MuiSwitch.styleOverrides.root['& .MuiSwitch-track'],
                        backgroundColor: '#2a2a2a',
                        border: '1px solid #888',
                    },
                },
            },
        },
        MuiTooltip: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiTooltip.styleOverrides,
                tooltip: {
                    ...commonBaseTheme.components.MuiTooltip.styleOverrides.tooltip,
                    color: WHITE,
                },
            },
        },
        MuiDivider: {
            styleOverrides: {
                ...commonBaseTheme.components.MuiDivider?.styleOverrides,
                root: {
                    ...commonBaseTheme.components.MuiDivider?.styleOverrides?.root,
                    borderColor: 'rgba(255, 255, 255, 0.2)', // Lighter for dark theme
                },
            },
        },
    },
});

export { lightTheme, darkTheme };
