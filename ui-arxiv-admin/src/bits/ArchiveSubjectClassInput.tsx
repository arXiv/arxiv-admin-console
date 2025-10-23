
import React, {useContext, useEffect, useState} from 'react';
import {useRecordContext, InputProps, useGetOne, useDataProvider, AutocompleteInput} from 'react-admin';
import {RuntimeContext} from "../RuntimeContext";
import {Typography, Box} from '@mui/material';

interface ArchiveSubjectClassInputProps extends InputProps {
    sourceCategory: string;
    sourceClass: string;
    fullWidth?: boolean;
}

interface Category {
    id: string,
    archive: string,
    subject_class: string,
    definitive: boolean,
    active: boolean,
    category_name: string,
    endorse_all: string,
    endorse_email: string,
    papers_to_endorse: boolean,
    endorsement_domain: string
    name: string
}


const ArchiveSubjectClassInput: React.FC<ArchiveSubjectClassInputProps> = ({ sourceCategory, sourceClass, source, ...rest }) => {
    const [categories, setCategories] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const runtimeProps = useContext(RuntimeContext);

    useEffect(() => {
        const fetchCategories = async () => {
            const url = `${runtimeProps.ADMIN_API_BACKEND_URL}/v1/categories/`;
            try {
                const response = await fetch(url);
                const data = await response.json();

                // Filter active categories
                const activeCategories = data.filter((cat: Category) => cat.active);

                // Group all categories by endorsement_domain
                const byDomain = new Map<string, any[]>();
                activeCategories.forEach((cat: Category) => {
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
            } catch (error) {
                console.error('Failed to fetch category', error);
                setCategories([]);
            } finally {
                setLoading(false);
            }
        };

        fetchCategories();

    }, [runtimeProps.ADMIN_API_BACKEND_URL]);

    const optionRenderer = (choice: any) => (
        <Box>
            <Typography variant="body1">{choice.name}</Typography>
            <Typography variant="body2" color="text.secondary">{choice.description}</Typography>
        </Box>
    );

    if (loading) {
        return <p>Loading categories...</p>;
    }

    return (
        <AutocompleteInput
            label={"Categories"}
            source={source}
            choices={categories}
            groupBy={(option) => option.group}
            optionText={optionRenderer}
            inputText={(choice) => `${choice.name} - ${choice.description}`}
            helperText={false}
            {...rest}
        />
    );
};

export default ArchiveSubjectClassInput;
