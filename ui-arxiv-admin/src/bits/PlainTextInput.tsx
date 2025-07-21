import React from 'react';
import { TextInput, TextInputProps } from 'react-admin';

interface PlainTextInputProps extends TextInputProps {
    fontSize?: string;
    resizable?: boolean | 'horizontal' | 'vertical' | 'both';
}

const PlainTextInput: React.FC<PlainTextInputProps> = ({
                                                           fontSize = '1rem',
                                                           label = false,
                                                           helperText = false,
                                                           resizable = false,
                                                           sx,
                                                           ...rest
                                                       }) => {
    const getResizeValue = () => {
        if (resizable === true || resizable === 'both') return 'both';
        if (resizable === 'horizontal') return 'horizontal';
        if (resizable === 'vertical') return 'vertical';
        return 'none';
    };

    return (
    <TextInput
        label={label}
        helperText={helperText}
        sx={{
            '& .MuiInputBase-input': {
                fontSize,
                padding: '0px 8px',
                minHeight: 'auto',
                resize: getResizeValue(),
                overflow: 'auto'
            },
            '& .MuiOutlinedInput-root': {
                '& fieldset': {
                    border: 'none'
                },
                '&:hover fieldset': {
                    border: 'none'
                },
                '&.Mui-focused fieldset': {
                    border: 'none'
                }
            },
            '& .MuiInputBase-root': {
                minHeight: 'auto'
            },
            ...sx
        }}
        multiline={resizable !== false}
        {...rest}
    />
    );
};

export default PlainTextInput;

