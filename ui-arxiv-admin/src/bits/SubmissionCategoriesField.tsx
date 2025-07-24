import React, { useEffect, useState } from 'react';
import {useRecordContext, useDataProvider, RecordContextProvider, FieldProps} from 'react-admin';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from "@mui/material/CircularProgress";
import CategoryField from "./CategoryField";
import PrimaryIcon from '@mui/icons-material/Star';
import PublishedIcon from '@mui/icons-material/Newspaper';

interface SubmissionCategory {
    category: string;
    is_primary: boolean;
    is_published: boolean | null;
}

interface CategoryListProps {
    categories: SubmissionCategory[];
}

export const CategoryList: React.FC<CategoryListProps> = ({categories}) => {
    const is_published = categories.some((category) => category.is_published);

    return (
        <Box
            sx={{
                display: 'inline-flex !important',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'flex-start !important',
                gap: 1,
                width: 'auto !important'
        }}
        >
            {
                categories.map((category, index) => (
                    <Box
                        key={category.category}
                        sx={{
                            whiteSpace: 'nowrap',
                            textOverflow: 'ellipsis'
                        }}
                    >
                        <RecordContextProvider value={{
                            sourceCategory: category.category.split('.')[0] || '',
                            sourceClass: category.category.split('.')[1] || null
                        }}>
                            <CategoryField source={category.category} sourceCategory="sourceCategory" sourceClass="sourceClass"
                                           primary={index === 0} renderAs={"chip"}
                            />
                        </RecordContextProvider>
                    </Box>
                ))
            }
        </Box>
    );
}


const SubmissionCategoriesField: React.FC = () => {
    const record = useRecordContext<{ last_submission_id: number | null, abs_categories: string }>();
    const dataProvider = useDataProvider();
    const [categories, setCategories] = useState<
        {
            id: number;
            categories: SubmissionCategory[];
        } | null
    >(null);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        console.log("submission: " + JSON.stringify(record));
        if (record?.last_submission_id === null) {
            if (record?.abs_categories) {
                setCategories(
                    {
                        id: 0,
                        categories: record.abs_categories.split(',').map((category) => ({
                            category: category,
                            is_primary: false,
                            is_published: null,
                            }
                        ))
                    }
                )
            }
            setLoading(false);
        } else {
            if (record?.last_submission_id) {
                const fetchCategories1 = async () => {
                    try {
                        setLoading(true);
                        // Fetch categories using getOne()
                        const {data} = await dataProvider.getOne('submission_categories', {
                            id: record.last_submission_id,
                        });
                        console.log("submission categories: " + JSON.stringify(data));
                        setCategories(data);
                    } catch (error) {
                        console.error('Error fetching submission categories:', error);
                        setCategories(null);
                    } finally {
                        setLoading(false);
                    }
                };

                fetchCategories1();
            }
            else
                setLoading(false);
        }
    }, [record, dataProvider]);

    if (!record) return null;

    if (loading) {
        return <CircularProgress />;
    }

    if (!categories || categories.categories.length === 0) {
        return <Typography>No categories available</Typography>;
    }

    return (
        <CategoryList categories={categories.categories} />
    );
};

export default SubmissionCategoriesField;