#ifndef DIALOG_H
#define DIALOG_H

#include <QDialog>

QT_BEGIN_NAMESPACE
namespace Ui { class Dialog; }
QT_END_NAMESPACE

class Dialog : public QDialog
{
    Q_OBJECT

public:
    Dialog(QWidget *parent = nullptr);
    ~Dialog();

private slots:
    void on_pushButton_clicked();

    void on_pushButton_clicked(bool checked);

    void on_checkBox_3_toggled(bool checked);

    void on_checkBox_clicked();

    void on_checkBox_2_clicked(bool checked);

private:
    Ui::Dialog *ui;
};
#endif // DIALOG_H
