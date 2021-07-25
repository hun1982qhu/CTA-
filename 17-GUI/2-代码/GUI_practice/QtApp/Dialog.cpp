#include "Dialog.h"
#include "ui_Dialog.h"

Dialog::Dialog(QWidget *parent)
    : QDialog(parent)
    , ui(new Ui::Dialog)
{
    ui->setupUi(this);
}

Dialog::~Dialog()
{
    delete ui;
}


void Dialog::on_pushButton_clicked()
{

}


void Dialog::on_checkBox_3_toggled(bool checked)
{

}


void Dialog::on_checkBox_clicked()
{

}


void Dialog::on_checkBox_2_clicked(bool checked)
{

}

