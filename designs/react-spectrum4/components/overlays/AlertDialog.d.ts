import type {ReactElement, ReactNode} from 'react';

export interface AlertDialogProps {
  title?: string;
  children?: ReactNode;
  primaryActionLabel?: string;
  secondaryActionLabel?: string;
  cancelLabel?: string;
  variant?: 'confirmation' | 'information' | 'destructive' | 'error' | 'warning';
}

export declare function AlertDialog(props: AlertDialogProps): ReactElement;
