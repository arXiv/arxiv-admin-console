
import React, {useContext, useEffect, useState, ReactNode} from 'react';
import {useRecordContext, FieldProps, } from 'react-admin';
import Tooltip from '@mui/material/Tooltip';
import {RuntimeContext} from "../RuntimeContext";
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';

interface CategoryFieldProps extends FieldProps {
    sourceCategory: string;
    sourceClass: string;
    renderAs?: "chip" | "text";
    primary?: boolean;
}

const CategoryField: React.FC<CategoryFieldProps> = ({ sourceCategory, sourceClass, renderAs, primary }) => {
    const record = useRecordContext<{ [key: string]: string }>();
    const [hovered, setHovered] = useState(false); // Track whether the mouse is over the element
    const [categoryName, setCategoryName] = useState<string | null>(null); // Store the fetched category name
    const [loading, setLoading] = useState<boolean>(false);
    const runtimeProps = useContext(RuntimeContext);

    useEffect(() => {

        if (hovered && !categoryName && record && record[sourceCategory]) {
            setLoading(true);

            const fetchCategory = async () => {
                const url = `${runtimeProps.ADMIN_API_BACKEND_URL}/categories/${record[sourceCategory]}/subject-class/${record[sourceClass] || "*"}`;
                try {
                    const response = await fetch(url);
                    // const text = await response.clone().text()
                    const data = await response.json();
                    setCategoryName(data?.category_name || 'No category name');
                } catch (error) {
                    console.error('Failed to fetch category', error);
                    setCategoryName('No category name');
                } finally {
                    setLoading(false);
                }
            };

            fetchCategory();
        }
    }, [hovered, categoryName, record, sourceCategory, sourceClass]);

    if (!record) return null;

    const categoryText = record[sourceCategory] + "." + (record[sourceClass] || '*');

    const renderContent = (): ReactNode => {
        const label = <Typography fontWeight={primary ? "bolder" : "normal" } component={"span"} sx={{m:0, p:0}}>{primary ? "(Primary) " : ""}{categoryText}</Typography>;
        switch (renderAs) {
            case 'chip':
                return (
                    <Chip
                        size={"small"}
                        key={categoryText}
                        label={label}  // Use text directly instead of Typography component
                    />
                );
            default:
                return label;
        }
    };

    return (
        <Tooltip title={loading ? 'Loading...':  categoryName || 'No category name'}>
            <span
                onMouseEnter={() => setHovered(true)}  // Trigger hover
            >
                {renderContent()}
            </span>
        </Tooltip>
    );
};

export default CategoryField;