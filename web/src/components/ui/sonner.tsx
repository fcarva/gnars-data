import { useEffect, useState, type ComponentProps } from "react";
import { Toaster as SonnerToaster, toast } from "sonner";

type ToasterProps = ComponentProps<typeof SonnerToaster>;

const resolveTheme = () => {
  const fromDom = document.documentElement.dataset.theme;
  if (fromDom === "light" || fromDom === "dark") {
    return fromDom;
  }
  return "system";
};

const Toaster = ({ ...props }: ToasterProps) => {
  const [theme, setTheme] = useState<ToasterProps["theme"]>("system");

  useEffect(() => {
    setTheme(resolveTheme() as ToasterProps["theme"]);
  }, []);

  return (
    <SonnerToaster
      theme={theme}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: "group toast",
          description: "group-[.toast]:text-muted-foreground",
          actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
