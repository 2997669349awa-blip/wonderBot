export {};

declare global {
  interface WonderBotDesktopAppUpdateCheckResult {
    ok: boolean;
    reason?: string | null;
    currentVersion?: string;
    latestVersion?: string | null;
    hasUpdate: boolean;
  }

  interface WonderBotDesktopAppUpdateResult {
    ok: boolean;
    reason?: string | null;
  }

  interface WonderBotDesktopAppUpdateProgress {
    phase: "downloading" | "verifying" | "installing";
    downloadedBytes: number;
    totalBytes?: number | null;
  }

  interface WonderBotAppUpdaterBridge {
    checkForAppUpdate: () => Promise<WonderBotDesktopAppUpdateCheckResult>;
    installAppUpdate: (
      onProgress?: (progress: WonderBotDesktopAppUpdateProgress) => void,
    ) => Promise<WonderBotDesktopAppUpdateResult>;
  }

  interface Window {
    astrbotAppUpdater?: WonderBotAppUpdaterBridge;
    astrbotDesktop?: {
      isDesktop: boolean;
      isDesktopRuntime: () => Promise<boolean>;
      getBackendState: () => Promise<{
        running: boolean;
        spawning: boolean;
        restarting: boolean;
        canManage: boolean;
      }>;
      restartBackend: (authToken?: string | null) => Promise<{
        ok: boolean;
        reason: string | null;
      }>;
      stopBackend: () => Promise<{
        ok: boolean;
        reason: string | null;
      }>;
      pickDirectory?: (defaultPath?: string | null) => Promise<string | null>;
      setWindowTheme?: (theme: 'dark' | 'light' | null) => Promise<{
        ok: boolean;
        reason: string | null;
      }>;
      minimizeWindow?: () => Promise<{
        ok: boolean;
        reason: string | null;
      }>;
      toggleMaximizeWindow?: () => Promise<{
        ok: boolean;
        reason: string | null;
      }>;
      closeWindow?: () => Promise<{
        ok: boolean;
        reason: string | null;
      }>;
      onTrayRestartBackend?: (callback: () => void) => () => void;
    };
  }
}
