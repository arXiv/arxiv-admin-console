import React from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import {InputProps, useInput} from "react-admin";

type FlagType = {
    value: string,
    label: string,
};

interface FlagInputProps extends InputProps {
    source: string;
}


const SourceFlagsInput: React.FC<FlagInputProps> = ({source, ...inputProps}) => {
    const flagOptions: FlagType[] = [
        {value: "S", label: "encrypted"},
        {value: "A", label: "ancillary"},
        {value: "B", label: "pilot data"},
        {value: "1", label: "Single File"},
        {value: "D", label: "Deleted"},
    ];

    // Use react-admin's useInput hook to handle form state
    const {
        field: { value, onChange },
        fieldState: { error }
    } = useInput({ source, ...inputProps });

    // Split each character
    const selectedFlags = value ? value.split("") : [];

    // Convert flag strings to full flag objects
    const selectedOptions = selectedFlags.map((fv: string) => {
        return flagOptions.find(flag => flag.value === fv);
    }).filter(Boolean);


    const handleSelectionChange = (newSelectedOptions: typeof selectedOptions) => {
        // Convert selected flags back to string
        const flagStrings = newSelectedOptions.map((option: NonNullable<typeof selectedOptions[0]>) =>
            option.value
        );
        const newValue = flagStrings.join('');
        onChange(newValue);
    };

    return (
        <Autocomplete
            multiple
            size="small"
            options={flagOptions}
            getOptionLabel={(option) => option.label ?? "Unknown Flag"}
            isOptionEqualToValue={(option, value) =>
                option.value && value.value && option.value === value.value
            }
            renderInput={(params) => <TextField
                {...params}
                label={false}
                error={!!error}
                helperText={false}
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
                        'aria-label': 'Flags',
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
            disableCloseOnSelect
            value={selectedOptions}
            onChange={(_event, newValue) => handleSelectionChange(newValue)}
        />
    );
};

export default SourceFlagsInput;
