import React, { useState } from "react";
import { useRecordContext, useRefresh } from "react-admin";
import {Switch, FormControlLabel, FormControl, SxProps} from "@mui/material";
import UserFlagDialog, { UserFlagOption } from "./UserFlagDialog";

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
        switch (source) {
            case 'flag_suspect':
                return {
                    title: "Update User Suspect Status",
                    flagKey: "flag_suspect",
                    options: [{ key: "flag_suspect", label: "Flagged/Suspect", description: "Mark user as suspect for administrative review" }]
                };
            case 'flag_banned':
                return {
                    title: "Update User Ban Status",
                    flagKey: "flag_banned",
                    options: [{ key: "flag_banned", label: "Banned", description: "Ban user from the system" }]
                };
            case 'flag_deleted':
                return {
                    title: "Update User Deleted Status", 
                    flagKey: "flag_deleted",
                    options: [{ key: "flag_deleted", label: "Deleted", description: "Mark user as deleted" }]
                };
            default:
                return {
                    title: `Update ${label}`,
                    flagKey: source,
                    options: [{ key: source, label: label, description: `Update ${label} status` }]
                };
        }
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