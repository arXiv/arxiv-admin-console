import React, { useEffect, useState } from "react";
import { AutocompleteInput, useDataProvider, useNotify, InputProps } from "react-admin";

interface CategoryListInputProps extends InputProps {
    label?: string;
}

const CategoryListInput: React.FC<CategoryListInputProps> = ({
    source,
    label = "Category",
    ...rest
}) => {
    const [categories, setCategories] = useState<any[]>([]);
    const dataProvider = useDataProvider();
    const notify = useNotify();

    useEffect(() => {
        async function getCategories() {
            try {
                const response = await dataProvider.getList("categories", {
                    pagination: { page: 1, perPage: 1000 },
                    sort: { field: 'archive', order: 'ASC' },
                    filter: { active: true }
                });
                const categoryOptions = response.data.map((cat: any) => ({
                    id: `${cat.archive}.${cat.subject_class}`,
                    name: `${cat.archive}.${cat.subject_class} - ${cat.category_name ?? "Unknown Category"}`
                }));
                setCategories(categoryOptions);
            } catch (error: any) {
                const msg = "Error fetching categories: " + error?.data?.detail;
                notify(msg, { type: "warning" });
                console.error(msg);
            }
        }
        getCategories();
    }, [dataProvider, notify]);

    return (
        <AutocompleteInput
            source={source}
            label={label}
            choices={categories}
            {...rest}
        />
    );
};

export default CategoryListInput;
