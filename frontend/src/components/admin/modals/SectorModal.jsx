import { Button } from '../../ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Loader2, Sparkles } from 'lucide-react';
import { api } from '../../../services/api';
import { useToast } from '../../../hooks/use-toast';

const SectorModal = ({
  sectorModalOpen,
  setSectorModalOpen,
  sectorForm,
  setSectorForm,
  enhancingSector,
  setEnhancingSector,
  handleSaveSector,
}) => {
  const { toast } = useToast();

  const enhanceSector = async () => {
    setEnhancingSector(true);
    try {
      const response = await api.post('/api/admin/ai-enhance', {
        type: 'sector',
        title: sectorForm.name,
        description: sectorForm.description,
      });
      if (response.data.status === 'success') {
        setSectorForm((current) => ({
          ...current,
          name: response.data.enhanced_title || current.name,
          description: response.data.enhanced_description || current.description,
        }));
        toast({ title: 'Sector refined', description: 'The name and description were updated.', duration: 3000 });
      } else {
        toast({ title: 'Enhancement failed', description: response.data.message, variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Enhancement failed', description: error.response?.data?.message || error.message, variant: 'destructive' });
    } finally {
      setEnhancingSector(false);
    }
  };

  return (
    <Dialog open={sectorModalOpen} onOpenChange={setSectorModalOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create sector</DialogTitle>
          <DialogDescription>Group related roles and define the email alias used by that hiring team.</DialogDescription>
        </DialogHeader>

        <form
          className="space-y-5"
          onSubmit={(event) => {
            event.preventDefault();
            handleSaveSector();
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="sector-name">Sector name</Label>
            <Input
              id="sector-name"
              autoFocus
              value={sectorForm.name}
              onChange={(event) => setSectorForm({ ...sectorForm, name: event.target.value })}
              placeholder="Product Engineering"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="sector-description">Description</Label>
            <textarea
              id="sector-description"
              value={sectorForm.description}
              onChange={(event) => setSectorForm({ ...sectorForm, description: event.target.value })}
              className="min-h-24 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="Describe the roles and responsibilities grouped in this sector."
            />
          </div>
          {sectorForm.name || sectorForm.description ? (
            <Button type="button" variant="outline" disabled={enhancingSector} onClick={enhanceSector}>
              {enhancingSector ? <Loader2 className="animate-spin" /> : <Sparkles className="text-blue-700" />}
              {enhancingSector ? 'Refining copy' : 'Refine with AI'}
            </Button>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="sector-email-alias">Email alias</Label>
            <Input
              id="sector-email-alias"
              type="email"
              value={sectorForm.email_alias}
              onChange={(event) => setSectorForm({ ...sectorForm, email_alias: event.target.value })}
              placeholder="engineering@example.com"
            />
          </div>

          <DialogFooter className="border-t pt-5">
            <Button type="button" variant="outline" onClick={() => setSectorModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={!sectorForm.name.trim()}>Create sector</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default SectorModal;
