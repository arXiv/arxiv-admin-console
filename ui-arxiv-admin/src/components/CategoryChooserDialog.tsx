import React, {useEffect, useState} from "react";
import {
    Dialog,
    DialogContent,
    DialogActions,
    DialogTitle,
    Button,
    Box,
    List,
    ListItem,
    ListItemText,
} from "@mui/material";

import Checkbox from '@mui/material/Checkbox';

import {paths as adminApi} from '../types/admin-api';
import {useDataProvider} from "react-admin";
import MuiTextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";

type CategoryT = adminApi['/v1/categories/']['get']['responses']['200']['content']['application/json'][0];

const CategoryChooserDialog: React.FC<
    {
        title: string;
        open: boolean;
        setOpen: (open: boolean) => void;
        currentCategories: Map<string, boolean>;
        onUpdateCategory?: (cat_id: string, selections: Map<string, boolean>, on_or_off: boolean) => void;
        onSaveUpdates?: (selection: Map<string, boolean>) => Promise<void>;
        saveLabel?: string;
        setComment?: (comment: string) => void;
        comment?: string;
        isLoading?: boolean;
    }
> = ({
         title,
         open,
         setOpen,
         currentCategories,
         onUpdateCategory,
         onSaveUpdates,
         saveLabel,
         setComment,
         comment,
         isLoading
     }) => {
    const [allCategories, setAllCategories] = useState<Map<string, CategoryT>>(new Map());
    const dataProvider = useDataProvider();
    const [isSaving, setIsSaving] = useState(false);
    const [isCategoryLoading, setIsCategoryLoading] = useState(false);

    useEffect(() => {
        if (open) {
            const fetchAllCategories = async () => {
                try {
                    const {data} = await dataProvider.getList<CategoryT>('categories', {
                        pagination: {page: 1, perPage: 10000},
                        sort: {field: 'id', order: 'ASC'},
                        filter: {active: true},
                    });

                    const catMap = new Map<string, CategoryT>();
                    data.forEach((category) => catMap.set(category.id, category));
                    setAllCategories(catMap);
                } catch (error) {
                    console.error("Error fetching all categories:", error);
                }
            };

            fetchAllCategories();
        }
    }, [open, dataProvider]);

    const handleToggle = (category: CategoryT) => {
        if (onUpdateCategory) {
            const currentSelection = currentCategories.get(category.id);
            onUpdateCategory(category.id, currentCategories, !currentSelection);
        }
    };


    const handleSave = async (event: React.MouseEvent<HTMLButtonElement>) => {
        event.preventDefault();

        // Set saving state to disable the button
        setIsSaving(true);

        try {
            if (onSaveUpdates)
                await onSaveUpdates(currentCategories);
        } catch (error: any) {
            console.error("Error during save operations:", error);
        } finally {
            // Re-enable the button regardless of success or failure
            handleClose();
            setIsSaving(false);
        }

        handleClose();
    };

    const handleClose = () => {
        // Only allow closing if not in the middle of saving
        if (!isSaving) {
            setOpen(false);
        }
    };


    const commentInput = setComment ? (
        <MuiTextField
            value={comment} onChange={(e) => setComment(e.target.value)} label="Comment" multiline rows={2}
            fullWidth sx={{mt: 2}} variant="outlined"/>
    ) : null;

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="md">
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
                {
                    (isCategoryLoading || isLoading) ? <CircularProgress color="secondary"/> : (
                        <Box sx={{display: 'flex', flexDirection: 'column'}}>
                            <List sx={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: 1
                            }}>
                                {Array.from(allCategories.entries()).map(([key, cat]) => (
                                    <ListItem
                                        key={key}
                                        dense
                                        onClick={() => handleToggle(cat)}
                                        sx={{
                                            cursor: 'pointer',
                                            borderRadius: 0,
                                            flex: '0 0 calc(50% - 8px)',
                                            '@media (min-width: 900px)': {
                                                flex: '0 0 calc(33.333% - 8px)'
                                            },
                                            '@media (min-width: 1200px)': {
                                                flex: '0 0 calc(25% - 8px)'
                                            },
                                            '&:hover': {
                                                backgroundColor: '#8AF'
                                            },
                                            py: 0
                                        }}
                                    >
                                        <Checkbox
                                            edge="start"
                                            checked={!!currentCategories.get(cat.id)}
                                            tabIndex={-1}
                                            disableRipple
                                        />
                                        <ListItemText
                                            primary={`${cat.archive}.${cat.subject_class}`}
                                            secondary={cat.category_name}
                                            slotProps={{
                                                root: {sx: {py: 0, my: "2px"}}
                                            }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Box>
                    )
                }
                {commentInput}
            </DialogContent>
            <DialogActions>
                {onSaveUpdates ? (
                    <Button
                        onClick={handleSave}
                        variant="contained"
                        disabled={isSaving || isLoading || isCategoryLoading}
                    >
                        {isSaving ? "Saving..." : (saveLabel || "Save")}
                    </Button>
                ) : null}
                <Button onClick={handleClose} disabled={isSaving}>Cancel</Button>
            </DialogActions>
        </Dialog>
    );
};

export default CategoryChooserDialog;
