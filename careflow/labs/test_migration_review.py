from django.test import TransactionTestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from .test_processing import ProcessingFixture
from .models import LabOrder,LabReviewAssignment,LabResultReview,LabEvent
from careflow.clinical.models import Note


class ReviewBackfillMigrationTests(ProcessingFixture,TransactionTestCase):
    def test_populated_parent_upgrade_preserves_data_and_records_system_provenance(self):
        self.setup_processing(); pending=self.draft();cancelled=self.draft()
        from .services import cancel_order
        import uuid
        cancel_order(self.physician,cancelled.public_id,cancelled.version,'Synthetic draft cancelled',uuid.uuid4(),True)
        self.finish_encounter(); report=self.publish();self.physician.is_active=False;self.physician.save()
        order_id=self.order.pk; original_payload=report.payload; protected=list(Note.objects.values())
        with connection.cursor() as cursor:
            cursor.execute('SELECT payload FROM labs_labresult WHERE id=%s',[report.pk]);raw_payload=cursor.fetchone()[0]
        # Only this disposable test DB is downgraded; no user database is accessed.
        executor=MigrationExecutor(connection)
        executor.migrate([('labs','0002_labresult_remove_laborder_lab_order_state_times_and_more')])
        try:
            executor=MigrationExecutor(connection); executor.migrate([('labs','0004_labevent_system_source_alter_labevent_command_actor_and_more')])
            order=LabOrder.objects.get(pk=order_id); assignment=order.current_review_assignment
            self.assertIsNone(LabOrder.objects.get(pk=pending.pk).current_review_assignment_id);self.assertIsNone(LabOrder.objects.get(pk=cancelled.pk).current_review_assignment_id)
            self.assertFalse(assignment.physician.is_active)
            self.assertEqual(assignment.source,'migration_backfill');self.assertIsNone(assignment.assigned_by_id);self.assertEqual(assignment.physician_id,order.ordering_physician_id)
            with connection.cursor() as cursor:
                cursor.execute('SELECT payload FROM labs_labresult WHERE id=%s',[report.pk]);self.assertEqual(cursor.fetchone()[0],raw_payload)
            self.assertEqual(order.current_publication.payload,original_payload);self.assertFalse(LabResultReview.objects.exists())
            event=LabEvent.objects.get(system_source='migration_backfill');self.assertIsNone(event.command_actor_id);self.assertIsNone(event.command_key);self.assertEqual(event.review_assignment,assignment)
            self.assertEqual(protected,list(Note.objects.values()))
        finally:
            executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
