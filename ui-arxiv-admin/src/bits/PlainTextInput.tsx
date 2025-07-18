import React from 'react';
import { TextInput, TextInputProps } from 'react-admin';

interface PlainTextInputProps extends TextInputProps {
    fontSize?: string;
}

const PlainTextInput: React.FC<PlainTextInputProps> = ({
                                                           fontSize = '1rem',
                                                           label = false,
                                                           helperText = false,
                                                           sx,
                                                           ...rest
                                                       }) => (
    <TextInput
        label={label}
        helperText={helperText}
        sx={{
            '& .MuiInputBase-input': {
                fontSize,
                padding: '4px 0',
                minHeight: 'auto'
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
        {...rest}
    />
);

export default PlainTextInput;

