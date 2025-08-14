
import React, {useContext, useEffect, useState} from 'react';
import {useRecordContext, InputProps, useGetOne, useDataProvider, SelectArrayInput, choices} from 'react-admin';
import {RuntimeContext} from "../RuntimeContext";

interface CategoryInputFieldProps extends InputProps {
    sourceCategory: string;
    sourceClass: string;
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

const CategoryInputField: React.FC<CategoryInputFieldProps> = ({ sourceCategory, sourceClass, source }) => {
    const record = useRecordContext<{ [key: string]: string }>();
    const [categories, setCategories] = useState<[Category] | null>(null); // Store the fetched category name
    const [loading, setLoading] = useState<boolean>(true);
    const runtimeProps = useContext(RuntimeContext);

    useEffect(() => {
        const fetchCategories = async () => {
            const url = `${runtimeProps.ADMIN_API_BACKEND_URL}/v1/categories/`;
            try {
                const response = await fetch(url);
                const data = await response.json();
                const cats = data.map((cat: Category) => ({
                    ...cat,
                    name: `${cat.archive}.${cat.subject_class || "*"}`,
                }));
                setCategories(cats);
            } catch (error) {
                console.error('Failed to fetch category', error);
                setCategories(null);
            } finally {
                setLoading(false);
            }
        };

        fetchCategories();

    }, []);

    if (!record) return null;
    if (!categories) return null;

    console.log("submission: " + JSON.stringify(record));

    return (
        <>
            {loading ? (
                <p>Loading categories...</p>
            ) : (
                <SelectArrayInput
                    source={source}
                    choices={categories} // Use fetched categories
                    optionText="name" // Display category name
                    optionValue="id" // Use category ID for selection
                />
            )}
        </>
    );
};

export default CategoryInputField;
