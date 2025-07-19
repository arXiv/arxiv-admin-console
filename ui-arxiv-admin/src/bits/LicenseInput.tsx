import React, {useEffect} from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import {InputProps, useDataProvider, useInput, useNotify} from "react-admin";
import { paths as adminApi } from "../types/admin-api";

type LicensesType = adminApi["/v1/licenses/"]["get"]["responses"]["200"]["content"]["application/json"];
type LicenseType = LicensesType[0];

interface LicenseInputProps extends InputProps {
    source: string;
}


const LicenseInput: React.FC<LicenseInputProps> = ({source, ...inputProps}) => {
    const [licenseOptions, setLicenseOptions] = React.useState<LicensesType>([]);
    const dataProvider = useDataProvider();
    const notify = useNotify();

    useEffect(() => {
        async function getLicenses() {
            try {
                const response = await dataProvider.getList("licenses",
                    {
                        sort: { field: 'sequence', order: 'ASC' },
                    });
                setLicenseOptions(response.data);
            }
            catch (error) {
                // @ts-ignore
                notify(error.message, "warning");
            }
        }
        getLicenses();
    }, []);

    // Use react-admin's useInput hook to handle form state
    const {
        field: { value, onChange },
        fieldState: { error }
    } = useInput({ source, ...inputProps });


    // Convert option strings to full source format object
    const selectedOption = value ? licenseOptions.find(license => license.id === value) : null;

    const handleSelectionChange = (newSelectedOption: LicenseType | null) => {
        // Convert selected option back to string value or null
        const newValue = newSelectedOption ? newSelectedOption.id : null;
        onChange(newValue);
    };

    return (
        <Autocomplete
            size="small"
            options={licenseOptions}
            getOptionLabel={(option) => option.label ?? "Unknown Format"}
            isOptionEqualToValue={(option, value) =>
                option.id === value.id
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
                        'aria-label': 'Source Format',
                    }
                }}
            />}
            renderOption={(props, option) => (
                <li
                    {...props}
                    key={option.id}
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

export default LicenseInput;
