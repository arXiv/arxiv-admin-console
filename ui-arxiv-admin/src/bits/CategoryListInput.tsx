import React, { useEffect, useState } from "react";
import { AutocompleteInput, useDataProvider, useNotify, InputProps } from "react-admin";
import { SxProps, Typography, Box } from "@mui/material";

interface CategoryListInputProps extends InputProps {
    label?: string;
    sx?: SxProps;
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

                // Filter out inactive categories
                const activeCategories = response.data.filter((cat: any) => cat.active);

                // Group all categories by endorsement_domain
                const byDomain = new Map<string, any[]>();
                activeCategories.forEach((cat: any) => {
                    const domain = cat.endorsement_domain;
                    if (!byDomain.has(domain)) {
                        byDomain.set(domain, []);
                    }
                    byDomain.get(domain)!.push(cat);
                });

                // Build the options list
                const categoryOptions: any[] = [];

                // Sort domains to get consistent ordering
                const sortedDomains = Array.from(byDomain.keys()).sort();

                sortedDomains.forEach((domain) => {
                    const domainCategories = byDomain.get(domain)!;

                    // Find the parent (non-definitive category with empty subject_class) for group label
                    const parent = domainCategories.find((cat: any) => !cat.definitive && cat.subject_class === '');
                    const groupLabel = parent
                        ? `${parent.archive} - ${parent.category_name ?? "Unknown Category"}`
                        : domain;

                    // Add all definitive categories (children) under this domain
                    const children = domainCategories.filter((cat: any) => cat.definitive);
                    children.forEach((cat: any) => {
                        const catId = cat.subject_class ? `${cat.archive}.${cat.subject_class}` : `${cat.archive}.`;
                        categoryOptions.push({
                            id: catId,
                            name: catId,
                            description: `${cat.category_name ?? "Unknown Category"}`,
                            group: groupLabel
                        });
                    });
                });

                setCategories(categoryOptions);
            } catch (error: any) {
                const msg = "Error fetching categories: " + error?.data?.detail;
                notify(msg, { type: "warning" });
                console.error(msg);
            }
        }
        getCategories();
    }, [dataProvider, notify]);

    const optionRenderer = (choice: any) => (
        <Box>
            <Typography variant="body1">{choice.name}</Typography>
            <Typography variant="body2" color="text.secondary">{choice.description}</Typography>
        </Box>
    );

    return (
        <AutocompleteInput
            source={source}
            label={label}
            choices={categories}
            groupBy={(option) => option.group}
            optionText={optionRenderer}
            inputText={(choice) => `${choice.name} - ${choice.description}` }
            {...rest}
        />
    );
};

export default CategoryListInput;
