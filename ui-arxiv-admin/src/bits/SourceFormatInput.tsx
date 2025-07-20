import React from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import {InputProps, useInput} from "react-admin";

type SourceFormatType = {
    value: string,
    label: string,
};

interface SourceFormatInputProps extends InputProps {
    source: string;
}


const SourceFormatInput: React.FC<SourceFormatInputProps> = ({source, ...inputProps}) => {
    const sourceFormatOptions: SourceFormatType[] = [
        {value: "tex", label: "TeX"},
        {value: "ps", label: "PostScript"},
        {value: "html", label: "NTML"},
        {value: "pdf", label: "PDF"},
        {value: "withdrawn", label: "Deleted"},
        {value: "pdftex", label: "pdftex"},
        {value: "docx", label: "docx"},
    ];

    // Use react-admin's useInput hook to handle form state
    const {
        field: { value, onChange },
        fieldState: { error }
    } = useInput({ source, ...inputProps });


    // Convert option strings to full source format object
    const selectedOption = value ? sourceFormatOptions.find(sourceFormat => sourceFormat.value === value) : null;

    const handleSelectionChange = (newSelectedOption: SourceFormatType | null) => {
        // Convert selected option back to string value or null
        const newValue = newSelectedOption ? newSelectedOption.value : null;
        onChange(newValue);
    };

    return (
        <Autocomplete
            size="small"
            options={sourceFormatOptions}
            getOptionLabel={(option) => option.label ?? "Unknown Format"}
            isOptionEqualToValue={(option, value) =>
                option.value === value.value
            }
            renderInput={(params) => <TextField
                {...params}
                label={false}
                error={!!error}
                helperText={false}
sx={{
                    '& .MuiAutocomplete-root': {
                        paddingTop: '0px !important'
                    },
                    '& .MuiFilledInput-root': {
                        paddingTop: '0px !important'
                    },
                    '& .MuiInputBase-input': {
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
                    }
                }}
                slotProps={{
                    inputLabel: {
                        shrink: true,
                        sx: {
                            ...params.InputLabelProps,
                            position: 'static',
                            transform: 'none',
                            fontSize: '1em',
                            color: 'black',
                            fontWeight: 'bold',
                            pb: '3px',
                        },
                    },
                    input: {
                        ...params.InputProps,
                        notched: false,
                        'aria-label': 'Source Format',
                    }
                }}
            />}
            renderOption={(props, option) => (
                <li
                    {...props}
                    key={option.value}
                    style={{
                        fontWeight: "normal",
                    }}
                >
                    {option.label}
                </li>
            )}
            value={selectedOption}
            onChange={(_event, newValue) => handleSelectionChange(newValue)}
        />
    );
};

export default SourceFormatInput;
