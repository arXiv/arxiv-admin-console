import React, {useContext, useEffect, useState} from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import DeleteIcon from "@mui/icons-material/Delete";
import { paths } from "../types/aaa-api";
import { paths as adminApi } from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext";
import {InputProps, useDataProvider, useInput} from "react-admin";
import Typography from "@mui/material/Typography";

export type CategoryType = adminApi["/v1/categories/{id}"]["get"]["responses"]["200"]["content"]["application/json"];
export type SubmitRequestType = paths["/account/register/"]['post']['requestBody']['content']['application/json'];
export type SelectedCategoryType = SubmitRequestType["default_category"] | null;


type CategoryGroupType = {
    group: string;
    subcategories: CategoryType[];
};

interface CategoryInputProps extends InputProps {
    source: string;
}


const CategoryInput: React.FC<CategoryInputProps> = ({source, ...inputProps}) => {
    const [categoryList, setCategoryList] = useState<CategoryType[]>([]);
    const [categories, setCategories] = useState<CategoryGroupType[]>([]);
    const dataProvider = useDataProvider();
    
    // Use react-admin's useInput hook to handle form state
    const {
        field: { value, onChange },
        fieldState: { error }
    } = useInput({ source, ...inputProps });
    
    // Parse space-separated categories from the field value
    const selectedCategories = value ? value.split(' ').filter(Boolean) : [];
    
    // Convert category strings to full category objects
    const selectedCategoryObjects = selectedCategories.map((catStr: string) => {
        const [archive, subject_class] = catStr.split('.');
        return categoryList.find(cat => 
            cat.archive === archive && cat.subject_class === subject_class
        );
    }).filter(Boolean);

    useEffect(() => {
        async function getCategories() {
            try {
                const response = await dataProvider.getList("categories", {
                    pagination: { page: 1, perPage: 1000 },
                    sort: { field: 'archive', order: 'ASC' },
                    filter: {}
                });
                setCategoryList(response.data);
            }
            catch (error) {
                console.error("Error fetching categories:", error);
            }
        }
        getCategories();
    }, [dataProvider]);

    useEffect(() => {
        const categoryGroups: CategoryGroupType[] = Object.values(
            categoryList.reduce<Record<string, CategoryGroupType>>((acc, category) => {
                if (!acc[category.archive]) {
                    acc[category.archive] = { group: category.archive, subcategories: [] };
                }
                acc[category.archive].subcategories.push(category);
                return acc;
            }, {})
        );
        setCategories(categoryGroups);
    }, [categoryList]);

    const categoryOptions = categories
        .flatMap((categoryGroup) => [
            { group: categoryGroup.group, label: categoryGroup.group.toUpperCase(), isHeader: true } as const, // Header
            ...categoryGroup.subcategories.map((category) => ({
                group: categoryGroup.group,
                label: `${categoryGroup.group}.${category.subject_class} - ${category.category_name ?? "Unknown Category"}`, // ✅ Fallback for null values
                value: category, // Store full `CategoryType` object
                isHeader: false,
            })),
        ])
        .sort((a, b) => a.group.localeCompare(b.group));

    // Convert selected category objects back to options for Autocomplete
    const selectedOptions = selectedCategoryObjects.map((cat: CategoryType) =>
        categoryOptions.find(option => 
            !option.isHeader && 
            option.value.archive === cat.archive && 
            option.value.subject_class === cat.subject_class
        )
    ).filter(Boolean);

    const handleAddCategory = (newSelectedOption: typeof categoryOptions[0] | null) => {
        if (newSelectedOption && !newSelectedOption.isHeader) {
            const categoryString = `${newSelectedOption.value.archive}.${newSelectedOption.value.subject_class}`;
            if (!selectedCategories.includes(categoryString)) {
                const newValue = selectedCategories.length > 0 
                    ? `${value} ${categoryString}` 
                    : categoryString;
                onChange(newValue);
            }
        }
    };

    const handleRemoveCategory = (categoryToRemove: string) => {
        const newCategories = selectedCategories.filter((cat: string) => cat !== categoryToRemove);
        const newValue = newCategories.join(' ');
        onChange(newValue || null);
    };

    const handleMoveUp = (index: number) => {
        if (index > 0) {
            const newCategories = [...selectedCategories];
            [newCategories[index - 1], newCategories[index]] = [newCategories[index], newCategories[index - 1]];
            onChange(newCategories.join(' '));
        }
    };

    const handleMoveDown = (index: number) => {
        if (index < selectedCategories.length - 1) {
            const newCategories = [...selectedCategories];
            [newCategories[index], newCategories[index + 1]] = [newCategories[index + 1], newCategories[index]];
            onChange(newCategories.join(' '));
        }
    };

    const availableOptions = categoryOptions.filter(option => 
        !option.isHeader && !selectedCategories.includes(`${option.value.archive}.${option.value.subject_class}`)
    );

    return (
        <Box>
            {/* Selected categories with ordering controls */}
            {selectedCategories.length > 0 && (
                <Box sx={{ mb: "4px" }}>
                    {selectedCategories.map((categoryStr: string, index: number) => {
                        const categoryObj = selectedCategoryObjects[index];
                        const categoryLabel = categoryObj 
                            ? `${categoryObj.archive}.${categoryObj.subject_class} - ${categoryObj.category_name ?? "Unknown Category"}`
                            : categoryStr;
                        
                        return (
                            <Box
                                key={categoryStr}
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    m: "2px",
                                    p: 0,
                                    border: 1,
                                    borderColor: 'divider',
                                    borderRadius: 1,
                                    backgroundColor: 'background.default'
                                }}
                            >
                                <IconButton
                                    size="small"
                                    onClick={() => handleMoveUp(index)}
                                    disabled={index === 0}
                                    sx={{
                                        p: 0,
                                        minWidth: '30px',
                                        width: '30px',
                                        height: '16px',
                                        borderRadius: 0,
                                        '&:disabled': { opacity: 0.3, backgroundColor: 'action.disabled' },
                                        '&:hover:not(:disabled)': { backgroundColor: 'action.hover' }
                                    }}
                                >
                                    <KeyboardArrowUpIcon sx={{ fontSize: '14px' }} />
                                </IconButton>
                                <IconButton
                                    size="small"
                                    onClick={() => handleMoveDown(index)}
                                    disabled={index === selectedCategories.length - 1}
                                    sx={{
                                        p: 0,
                                        minWidth: '30px',
                                        width: '30px',
                                        height: '16px',
                                        borderRadius: 0,
                                        '&:disabled': { opacity: 0.3, backgroundColor: 'action.disabled' },
                                        '&:hover:not(:disabled)': { backgroundColor: 'action.hover' }
                                    }}
                                >
                                    <KeyboardArrowDownIcon sx={{ fontSize: '14px' }} />
                                </IconButton>
                                {/*
                                <Box sx={{ fontSize: '0.875rem', color: 'text.primary' }}>
                                    {index === 0 && <strong>(Primary) </strong>}
                                    {categoryLabel}
                                </Box>
                                */}
                                <Typography component={"span"} variant="body2">
                                    {index === 0 && (
                                        <Typography
                                            component="span"
                                            variant="body2"
                                            fontWeight="bold"
                                        >
                                            (Primary)&nbsp;
                                        </Typography>
                                    )}
                                    {categoryLabel}
                                </Typography>
                                <Box sx={{ flex: 1 }} />
                                <IconButton
                                    size="small"
                                    onClick={() => handleRemoveCategory(categoryStr)}
                                    sx={{ ml: 1 }}
                                >
                                    <DeleteIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        );
                    })}
                </Box>
            )}
            
            {/* Autocomplete for adding new categories */}
            <Autocomplete
                size="small"
                options={availableOptions}
                groupBy={(option) => option.group.toUpperCase()}
                getOptionLabel={(option) => option.label ?? "Unknown Category"}
                sx={{
                    '& .MuiAutocomplete-root': {
                        paddingTop: "2px"
                    },
                    '& .MuiInputBase-root': {
                        paddingTop: "2px"
                    }
                }}
                renderInput={(params) => <TextField
                    {...params}
                    label={false}
                    placeholder="Add category..."
                    error={!!error}
                    helperText={error?.message}
                    slotProps={{
                        inputLabel: {
                            shrink: true,
                            sx: {
                                ...params.InputLabelProps,
                                position: 'static',
                                transform: 'none',
                                fontSize: '1em',
                                color: 'text.primary',
                                fontWeight: 'bold',
                                pb: '3px',
                            },
                        },
                        input: {
                            ...params.InputProps,
                            notched: false,
                            'aria-label': 'Add Category',
                        }
                    }}
                />}
                renderOption={(props, option) => (
                    <li
                        {...props}
                        key={option.isHeader ? option.group : option.value.id}
                        style={{
                            fontWeight: "normal",
                            paddingLeft: 16,
                        }}
                    >
                        {option.label}
                    </li>
                )}
                value={null}
                onChange={(_event, newValue) => handleAddCategory(newValue)}
            />
        </Box>
    );
};

export default CategoryInput;
