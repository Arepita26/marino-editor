export type AppTheme = "light" | "dark";

export type ProcessState = "IDLE" | "SELECTED" | "UPLOADING" | "PROCESSING" | "COMPLETED" | "ERROR";

export interface VideoMetadata {
  file: File;
  name: string;
  sizeBytes: number;
  sizeFormatted: string;
  previewUrl: string;
}

export interface ProcessingTicket {
  ticketId: string;
  status: "procesando" | "completado" | "error";
  progress: number;
  step?: string;
  error?: string;
  downloadUrl?: string;
}

export interface AppVersionInfo {
  version: string;
  buildTimestamp: number;
  releaseName: string;
  forceReload: boolean;
  changelog: string;
}
