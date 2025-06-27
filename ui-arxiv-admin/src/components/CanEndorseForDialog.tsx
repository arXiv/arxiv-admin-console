import React, {useEffect, useState} from "react";
import { paths as adminApi } from '../types/admin-api';
import {Identifier, useDataProvider, useRecordContext} from "react-admin";
import CategoryChooserDialog from "./CategoryChooserDialog";
import { CircularProgress, Box, Dialog, DialogTitle, DialogContent } from "@mui/material";

type CanEndorseForT = adminApi['/v1/users/{user_id}/can-endorse-for']['get']['responses']['200']['content']['application/json'][0];

const CanEndorseForDialog: React.FC<
    {
        open: boolean;
        setOpen: (open: boolean) => void;
    }
> = ({ open, setOpen }) => {
    const [canEndorseFor, setCanEndorseFor] = useState<Map<string, boolean> >( new Map<string, boolean>());
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const dataProvider = useDataProvider();
    const record = useRecordContext();
    const userId = record?.id as Identifier;

    useEffect(() => {
        if (userId && open) {
            console.log("fetching canEndorseFor for user " + userId);
            setIsLoading(true);

            const fetchCanEndorseFor = async () => {
                try {
                    const { data } = await dataProvider.getList<CanEndorseForT>('can_endorse_for', {
                        filter: { user_id: userId },
                        pagination: { page: 1, perPage: 1000 },
                        sort: { field: 'id', order: 'ASC' }
                    });

                    const cats = new Map<string, boolean>();
                    for (const domain of data) {
                        cats.set(domain.archive + "." + domain.subject_class, domain.positive);
                    }
                    setCanEndorseFor(cats);
                } catch (error) {
                    console.error("Error fetching moderation domains:", error);
                } finally {
                    setIsLoading(false);
                }
            };

            fetchCanEndorseFor();
        }
    }, [open, userId, dataProvider]);

    if (!userId) return null;
    if (!open) return null;


    return (
        <CategoryChooserDialog
            title="Can endorse for"
            open={open}
            setOpen={setOpen}
            currentCategories={canEndorseFor}
            isLoading={isLoading}
        />
    );
};

export default CanEndorseForDialog;
