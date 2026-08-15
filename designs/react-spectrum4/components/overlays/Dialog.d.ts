import type {ReactElement, ReactNode} from 'react';

export interface DialogProps {
  children?: ReactNode;
  size?: 'S' | 'M' | 'L';
  isDismissable?: boolean;
  onOpenChange?: (isOpen: boolean) => void;
}

export declare function Dialog(props: DialogProps): ReactElement;
