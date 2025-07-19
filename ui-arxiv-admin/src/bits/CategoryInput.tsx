import React, {useContext, useEffect, useState} from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { paths } from "../types/aaa-api";
import { paths as adminApi } from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext";
import {InputProps, useDataProvider, useInput} from "react-admin";

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

    const handleSelectionChange = (newSelectedOptions: typeof selectedOptions) => {
        // Convert selected categories back to space-separated string
        const categoryStrings = newSelectedOptions.map((option: NonNullable<typeof selectedOptions[0]>) => 
            `${option.value.archive}.${option.value.subject_class}`
        );
        const newValue = categoryStrings.join(' ');
        onChange(newValue);
    };

    return (
        <Autocomplete
            multiple
            size="small"
            options={categoryOptions.filter((cat) => !cat.isHeader)}
            groupBy={(option) => (!option.isHeader ? option.group.toUpperCase() : "")}
            getOptionLabel={(option) => option.label ?? "Unknown Category"}
            isOptionEqualToValue={(option, value) => 
                !option.isHeader && !value.isHeader && 
                option.value && value.value && 
                option.value.id === value.value.id
            }
            renderInput={(params) => <TextField
                {...params}
                label={false}
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
                            color: 'black',
                            fontWeight: 'bold',
                            pb: '3px',
                        },
                    },
                    input: {
                        ...params.InputProps,
                        notched: false,
                        'aria-label': 'Categories',
                    }
                }}
            />}
            renderOption={(props, option) => (
                <li
                    {...props}
                    key={option.isHeader ? `header-${option.group}` : option.value.id}
                    style={{
                        fontWeight: option.isHeader ? "bold" : "normal",
                        paddingLeft: option.isHeader ? 0 : 16,
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

export default CategoryInput;
