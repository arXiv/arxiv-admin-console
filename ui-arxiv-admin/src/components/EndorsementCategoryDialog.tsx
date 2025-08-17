import React, {useEffect, useState} from "react";
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography } from '@mui/material';

import { paths as adminApi } from '../types/admin-api';
import {useDataProvider, useNotify, useRefresh} from "react-admin";
import CategoryChooserDialog from "./CategoryChooserDialog";
import { useMessageDialog } from "./MessageDialog";

type EndorsementT = adminApi['/v1/endorsements/']['get']['responses']['200']['content']['application/json'][0];
type EndorsementCreateT = adminApi['/v1/endorsements/']['post']['requestBody']['content']['application/json'];


const EndorsementCategoryDialog: React.FC<
    {
        open: boolean;
        setOpen: (open: boolean) => void;
        userId: number;
    }
> = ({ open, setOpen, userId }) => {
    const [endorsementCategories0, setEndorsementCategories0] = useState<Map<string, boolean>>(new Map<string, boolean>());
    const [endorsementCategories, setEndorsementCategories] = useState<Map<string, boolean>>(new Map<string, boolean>());
    const [comment, setComment] = useState<string >("");
    const dataProvider = useDataProvider();
    const refresh = useRefresh();
    const notify = useNotify();
    const { showMessage } = useMessageDialog();

    useEffect(() => {
        if (open && userId) {
            const fetchEndorsements = async () => {
                try {
                    const { data } = await dataProvider.getList<EndorsementT>('endorsements', {
                        filter: { endorsee_id: userId },
                        pagination: { page: 1, perPage: 1000 },
                        sort: { field: 'id', order: 'ASC' }
                    });

                    const selection = new Map<string, boolean>()
                    for (const endorsement of data) {
                        const category = endorsement.archive + "." + endorsement.subject_class;
                        selection.set(category, true);
                    }

                    setEndorsementCategories0(selection);
                    setEndorsementCategories(selection);
                } catch (error) {
                    console.error("Error fetching endorsements:", error);
                }
            };

            fetchEndorsements();
        }
    }, [open, userId, dataProvider]);


    const handleUpdate = (cat_id: string, _cats: Map<string, boolean>, on_or_off: boolean) => {
        setEndorsementCategories(prevMap => {
            const newMap = new Map(prevMap);
            newMap.set(cat_id, on_or_off);
            return newMap;
        });
    };


    const handleSave = async () => {
        const deleteOperations: string[] = [];
        const createOperations: EndorsementCreateT[] = [];

        for (const [key, value] of endorsementCategories.entries()) {
            const [archive, subject_class] = key.split(".");

            if (!value) {
                const id = `${userId}+${archive}+${subject_class}`;
                deleteOperations.push(id);
            } else if (endorsementCategories0.get(key) !== value) {
                const endorsement: EndorsementCreateT = {
                    endorsee_id: String(userId),
                    endorser_id: "",
                    archive: archive,
                    subject_class: subject_class,
                    type_: "admin",
                    point_value: 10,
                    flag_valid: true,
                    flag_knows_personally: true,
                    flag_seen_paper: false,
                    comment: comment,
                };
                createOperations.push(endorsement);
            }
        }

        const errors: string[] = [];
        if (deleteOperations.length > 0) {
            try {
                await dataProvider.deleteMany('endorsements', { ids: deleteOperations });
            } catch (error: any) {
                const errorDetail = error?.body?.detail as string | undefined;
                if (errorDetail) {
                    errors.push(`Error removing endorsements: ` + errorDetail);
                } else {
                    errors.push(`Error removing endorsements`);
                }
                console.error("Error deleting endorsements:", error);
            }
        }

        for (const endorsement of createOperations) {
            try {
                const _response = await dataProvider.create('endorsements', { data: endorsement },);
            } catch (error: any) {
                const errorDetail = error?.body?.detail as string | undefined;
                if (errorDetail)
                    errors.push(`Error creating endorsement of ${endorsement.archive}.${endorsement.subject_class || '*'}: ` + errorDetail);
                else
                    errors.push(`Error creating endorsement of ${endorsement.archive}.${endorsement.subject_class || '*'}`);
                console.error("Error creating endorsement:", JSON.stringify(error));
            }
        }

        if (errors.length > 0) {
            showMessage("Endorsement Errors", errors.join("\n"));
        }

        refresh();
    };


    if (!endorsementCategories) return null;

    return (
        <CategoryChooserDialog
            title="Endorsement Categories"
            open={open}
            setOpen={setOpen}
            currentCategories={endorsementCategories}
            onUpdateCategory={handleUpdate}
            onSaveUpdates={handleSave}
            comment={comment}
            setComment={setComment}
        />

    );
};

export default EndorsementCategoryDialog;
