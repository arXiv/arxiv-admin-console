import React, { useState } from "react";
import { useRecordContext, useRefresh } from "react-admin";
import {Switch, FormControlLabel, FormControl, SxProps} from "@mui/material";
import UserFlagDialog, { UserFlagOption, defaultFlagOptions } from "./UserFlagDialog";

interface FlaggedToggleProps {
    source: string;
    label?: string;
    helperText?: boolean;
    sx?: SxProps;
    size?: string;
    disabled?: boolean;
    dialogTitle?: string;
    flagKey?: string;
    flagOptions?: UserFlagOption[];
}

const FlaggedToggle: React.FC<FlaggedToggleProps> = ({
    source,
    label = "Flagged",
    helperText = false,
    sx,
    size,
    disabled = false,
    dialogTitle,
    flagKey,
    flagOptions
}) => {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [pendingValue, setPendingValue] = useState<boolean | null>(null);
    const record = useRecordContext();
    const refresh = useRefresh();

    // Get current value from record
    const currentValue = record ? Boolean(record[source]) : false;

    const handleToggleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.checked;
        
        // Only show dialog if value is actually changing
        if (newValue !== currentValue) {
            setPendingValue(newValue);
            setDialogOpen(true);
        }
        
        // Always prevent the switch from changing visually until dialog is handled
        event.preventDefault();
    };

    const handleDialogClose = () => {
        setDialogOpen(false);
        setPendingValue(null);
        // No need to refresh since we're not changing anything on cancel
    };

    const handleFlagUpdated = () => {
        // Refresh the record to get updated data from the server
        refresh();
        setDialogOpen(false);
        setPendingValue(null);
    };

    // Default configuration based on source if not provided
    const getDefaultConfig = () => {
        return {
            title: "Update User status",
            flagKey: source,
            options: defaultFlagOptions.filter(option => option.key === source)
        };
    };

    const config = getDefaultConfig();
    const finalTitle = dialogTitle || config.title;
    const finalFlagKey = flagKey || config.flagKey;
    const finalFlagOptions = flagOptions || config.options;

    return (
        <>
            <FormControl sx={sx}>
                <FormControlLabel
                    control={
                        <Switch
                            checked={currentValue}
                            onChange={handleToggleChange}
                            size={size === "small" ? "small" : "medium"}
                            disabled={disabled}
                        />
                    }
                    label={label}
                />
            </FormControl>
            
            <UserFlagDialog
                open={dialogOpen}
                setOpen={handleDialogClose}
                onUpdated={handleFlagUpdated}
                title={finalTitle}
                initialFlag={finalFlagKey}
                flagOptions={finalFlagOptions}
                pendingValue={pendingValue}
            />
        </>
    );
};

export default FlaggedToggle;